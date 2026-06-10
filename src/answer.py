"""
Milestone 5 — grounded generation for The Unofficial Guide (GT campus dining).

ask(question) retrieves the top-k chunks (src/index.py), feeds them to Groq's
llama-3.3-70b-versatile under a strict grounding prompt, and returns the answer
plus the source documents. Two grounding guarantees:

  1. The model is told to answer ONLY from the provided sources and to reply with
     a fixed "I don't have enough information on that." when they don't cover the
     question. If retrieval returns nothing usable, we abstain without even calling
     the LLM.
  2. Source attribution is built programmatically from the retrieved chunks'
     metadata — it does not depend on the model remembering to cite.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

try:  # works whether imported as src.answer or run from inside src/
    from index import search
except ImportError:
    from src.index import search

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MODEL = "llama-3.3-70b-versatile"
TOP_K = 5
MAX_DISTANCE = 0.7           # drop egregiously weak matches before the LLM sees them
ABSTAIN = "I don't have enough information on that."

SYSTEM = (
    "You are The Unofficial Guide to Georgia Tech campus dining. Answer the "
    "question using ONLY the information in the numbered sources the user provides. "
    "Rules:\n"
    "- Use only facts stated in the sources. Do not add anything from your own "
    "knowledge or assumptions.\n"
    f'- If the sources do not contain enough information to answer, reply with '
    f'exactly: "{ABSTAIN}" and nothing else.\n'
    "- Cite the sources you use inline with their [S#] labels.\n"
    "- Be concise, and report what students actually say. If the sources disagree "
    "(for example different prices or different years), say so rather than picking "
    "one silently."
)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is not set — copy .env.example to .env.")
        _client = Groq(api_key=key)
    return _client


def _format_context(hits: list[dict]) -> str:
    blocks = []
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        blocks.append(f"[S{i}] {m['title']} ({m['source']})\n{h['text']}")
    return "\n\n".join(blocks)


def _sources(hits: list[dict]) -> list[dict]:
    """Unique source documents behind the retrieved chunks (for attribution)."""
    seen, out = set(), []
    for h in hits:
        m = h["metadata"]
        if m["source_file"] in seen:
            continue
        seen.add(m["source_file"])
        out.append({"title": m["title"], "source": m["source"], "url": m["url"]})
    return out


def ask(question: str, k: int = TOP_K, max_distance: float = MAX_DISTANCE) -> dict:
    hits = search(question, k=k, max_distance=max_distance)
    if not hits:
        return {"answer": ABSTAIN, "sources": [], "chunks": []}

    user = f"Sources:\n{_format_context(hits)}\n\nQuestion: {question}"
    resp = _get_client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    answer = resp.choices[0].message.content.strip()

    # If the model abstained, don't imply the retrieved docs answered the question.
    if answer.lower().startswith("i don't have enough information"):
        return {"answer": answer, "sources": [], "chunks": hits}

    # Attribute to the chunks the model actually cited ([S#]); fall back to all
    # retrieved chunks if it cited none, so attribution is always present.
    cited = {int(n) for n in re.findall(r"\[S(\d+)\]", answer)}
    used = [hits[i - 1] for i in sorted(cited) if 1 <= i <= len(hits)] or hits
    return {"answer": answer, "sources": _sources(used), "chunks": hits}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Is the Georgia Tech meal plan worth it?"
    r = ask(q)
    print(f"Q: {q}\n\n{r['answer']}\n")
    for s in r["sources"]:
        print(f"  • {s['title']} ({s['source']})")
