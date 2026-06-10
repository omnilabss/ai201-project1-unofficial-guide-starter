"""
Milestone 3 — ingestion + chunking for The Unofficial Guide (GT campus dining).

Loads the cleaned-ish text in documents/*.txt, finishes cleaning it (unicode
normalization + per-source boilerplate removal), and splits each document into
~700-char chunks using the line-then-sentence packing described in planning.md.
Every chunk keeps its source metadata (from documents/sources.json) so answers
can be cited later.

Output: chunks.json at the repo root — a list of {id, text, metadata}.

Run:  ./.venv/bin/python src/ingest.py
"""
from __future__ import annotations

import html
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "documents"
OUT = ROOT / "chunks.json"

# Chunking params (see planning.md → Chunking Strategy). The 900-char cap keeps
# chunks under all-MiniLM-L6-v2's 256-token limit with margin.
TARGET = 700
OVERLAP = 100
HARD_MAX = 900


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

_UNICODE = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ",
    " ": " ", "​": "", "﻿": "",
}

# Standalone nav/section/boilerplate lines (compared case-insensitively).
DROP_EXACT = {
    "advertising", "atlguide", "the spots", "general", "opinions", "life",
    "news", "sports", "entertainment", "back to profile home",
    "back to full profile", "report", "more", "poll",
    "get recruited by colleges", "find college scholarships",
    "explore campus life at similar colleges", "campus", "student life",
    "safety", "clubs & activities", "music", "party scene", "greek life",
    "campus quality",
}
DROP_PREFIX = ("photo credit:", "read next:", "posted on", "share this")
DROP_CONTAINS = ("rent out their garages", "don't hesitate to reach out",
                 "leasing team", "sapphire card")  # last = repeated Infatuation ad

# Truncate a doc from the first line that contains any of these (related-article
# / ad tails). Keyed by doc id.
TAIL_CUT = {
    7: ("season is over", "advertiser content from"),       # Rumble Seat
    11: ("if you have any questions", "haniya is one of rambler"),  # Rambler
    10: ("if you have any questions", "is one of rambler"),  # Rambler
}

_DATE_RE = re.compile(
    r"^(?:\d{1,2}/\d{1,2}/\d{2,4}"
    r"|[A-Z][a-z]{2,8}\.? \d{1,2},? \d{4}.*)$"
)
_BYLINE_RE = re.compile(
    r"^[Bb]y\s+[A-Z][\w.'’-]+(?:\s+[A-Z&][\w.'’-]+){0,4}$"
)
_ON_DATE_IN_RE = re.compile(r"^on .+ in$", re.I)
_URL_RE = re.compile(r"^https?://\S+$")
_RATING_RE = re.compile(r"^Rating:", re.I)


def _normalize(text: str) -> str:
    text = html.unescape(text)
    for bad, good in _UNICODE.items():
        text = text.replace(bad, good)
    return text


def _niche_food_only(lines: list[str]) -> list[str]:
    """Niche page is a whole campus-life profile; keep only the Food block."""
    try:
        start = next(i for i, ln in enumerate(lines) if ln.lower() == "food")
    except StopIteration:
        return lines
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].lower() in {"campus quality", "campus"}), len(lines))
    return lines[start:end]


def _cut_after_last_rating(lines: list[str]) -> list[str]:
    """Infatuation guide: each spot ends in a 'Rating: x.x' line; everything
    after the last one is related-guide promo."""
    idxs = [i for i, ln in enumerate(lines) if _RATING_RE.match(ln)]
    return lines[: idxs[-1] + 1] if idxs else lines


def _truncate_at(lines: list[str], needles: tuple[str, ...]) -> list[str]:
    for i, ln in enumerate(lines):
        low = ln.lower()
        if any(n in low for n in needles):
            return lines[:i]
    return lines


def _strip_technique_byline(lines: list[str]) -> list[str]:
    """Drop the Technique 'on <date> in' line and the author name above it."""
    drop = set()
    for i, ln in enumerate(lines):
        if _ON_DATE_IN_RE.match(ln):
            drop.add(i)
            if i - 1 >= 0:
                drop.add(i - 1)
    return [ln for i, ln in enumerate(lines) if i not in drop]


def clean(raw: str, doc_id: int) -> list[str]:
    lines = [ln.strip() for ln in _normalize(raw).split("\n")]
    lines = [ln for ln in lines if ln]

    if doc_id == 13:
        lines = _niche_food_only(lines)
    if doc_id == 9:
        lines = _cut_after_last_rating(lines)
    if doc_id in TAIL_CUT:
        lines = _truncate_at(lines, TAIL_CUT[doc_id])

    lines = _strip_technique_byline(lines)

    kept = []
    for ln in lines:
        low = ln.lower()
        if low in DROP_EXACT:
            continue
        if low.startswith(DROP_PREFIX):
            continue
        if any(s in low for s in DROP_CONTAINS):
            continue
        if _URL_RE.match(ln) or _DATE_RE.match(ln) or _BYLINE_RE.match(ln):
            continue
        kept.append(ln)
    return kept


# ---------------------------------------------------------------------------
# Chunking — greedy line-then-sentence packing with overlap (planning.md)
# ---------------------------------------------------------------------------

def _sentence_split(text: str, hard_max: int) -> list[str]:
    sents = re.split(r"(?<=[.!?]) +", text)
    pieces, cur = [], ""
    for s in sents:
        if cur and len(cur) + 1 + len(s) > hard_max:
            pieces.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        pieces.append(cur)
    # any single sentence still too long → hard character split (last resort)
    out = []
    for p in pieces:
        while len(p) > hard_max:
            out.append(p[:hard_max])
            p = p[hard_max:]
        if p:
            out.append(p)
    return out


def _overlap_tail(lines: list[str], overlap: int) -> list[str]:
    out: list[str] = []
    total = 0
    for ln in reversed(lines):
        if out and total + len(ln) > overlap:
            break
        out.insert(0, ln)
        total += len(ln)
    return out


def _merge_small(chunks: list[str], min_len: int, hard_max: int) -> list[str]:
    """Fold a too-short chunk into a neighbour when it fits — avoids tiny
    fragments like a standalone 'North Ave Dining Hall' line, or a restaurant
    name/metadata header separated from its blurb. Prefers the previous chunk,
    falls back to the next (which keeps a leading header attached to its blurb)."""
    chunks = list(chunks)
    i = 0
    while i < len(chunks):
        if len(chunks[i]) >= min_len:
            i += 1
            continue
        if i > 0 and len(chunks[i - 1]) + 1 + len(chunks[i]) <= hard_max:
            chunks[i - 1] = f"{chunks[i - 1]}\n{chunks[i]}"
            del chunks[i]
            i = max(0, i - 1)
        elif i + 1 < len(chunks) and len(chunks[i]) + 1 + len(chunks[i + 1]) <= hard_max:
            chunks[i + 1] = f"{chunks[i]}\n{chunks[i + 1]}"
            del chunks[i]
        else:
            i += 1
    return chunks


def chunk_text(lines: list[str], target=TARGET, overlap=OVERLAP,
               hard_max=HARD_MAX) -> list[str]:
    # expand any over-long line into sentence-sized units first
    units: list[str] = []
    for ln in lines:
        units.extend([ln] if len(ln) <= hard_max
                     else _sentence_split(ln, hard_max))

    chunks: list[str] = []
    cur: list[str] = []
    for u in units:
        if cur and len("\n".join(cur + [u])) > target:
            chunks.append("\n".join(cur).strip())
            new = _overlap_tail(cur, overlap) + [u]
            # never let the carried-over overlap push a chunk past the cap
            if len("\n".join(new)) > hard_max:
                new = [u]
            cur = new
        else:
            cur.append(u)
    if cur:
        chunks.append("\n".join(cur).strip())

    chunks = [c for c in chunks if c.strip()]
    return _merge_small(chunks, min_len=150, hard_max=hard_max)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_chunks() -> list[dict]:
    manifest = json.loads((DOCS / "sources.json").read_text(encoding="utf-8"))
    out = []
    for entry in manifest:
        raw = (DOCS / entry["file"]).read_text(encoding="utf-8")
        lines = clean(raw, entry["id"])
        for n, text in enumerate(chunk_text(lines)):
            out.append({
                "id": f"{entry['id']:02d}-{n}",
                "text": text,
                "metadata": {
                    "doc_id": entry["id"],
                    "source_file": entry["file"],
                    "title": entry["title"],
                    "source": entry["source"],
                    "type": entry["type"],
                    "url": entry["url"],
                    "retrieved_via": entry.get("retrieved_via", ""),
                },
            })
    return out


def _count_tokens(texts: list[str]):
    """Accurate token counts via the MiniLM tokenizer (fast `tokenizers` lib,
    no torch import). Returns None if it can't be loaded."""
    try:
        from tokenizers import Tokenizer
        tok = Tokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    except Exception as e:  # noqa: BLE001
        print(f"(token check skipped: {type(e).__name__})")
        return None
    tok.no_truncation()  # IMPORTANT: default truncates at 128 → would mask over-long chunks
    return [len(tok.encode(t).ids) for t in texts]  # includes [CLS]/[SEP]


def main() -> None:
    chunks = build_chunks()
    OUT.write_text(json.dumps(chunks, indent=2, ensure_ascii=False),
                   encoding="utf-8")

    texts = [c["text"] for c in chunks]
    lens = [len(t) for t in texts]
    per_doc: dict[int, int] = {}
    for c in chunks:
        per_doc[c["metadata"]["doc_id"]] = per_doc.get(c["metadata"]["doc_id"], 0) + 1

    print(f"Wrote {len(chunks)} chunks -> {OUT.relative_to(ROOT)}")
    print(f"chars: min {min(lens)}  median {int(statistics.median(lens))}  "
          f"mean {int(statistics.mean(lens))}  max {max(lens)}")
    assert max(lens) <= HARD_MAX, "A chunk exceeds the character hard cap!"
    print("chunks per doc:", {k: per_doc[k] for k in sorted(per_doc)})
    print("empty chunks:", sum(1 for t in texts if not t.strip()))

    toks = _count_tokens(texts)
    if toks:
        over = sum(1 for n in toks if n > 256)
        print(f"tokens: max {max(toks)}  >256: {over}")
        assert over == 0, "A chunk exceeds the 256-token MiniLM limit!"


if __name__ == "__main__":
    main()
