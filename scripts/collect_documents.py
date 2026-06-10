"""
Milestone 1 document collector — The Unofficial Guide (Georgia Tech campus dining).

Downloads each source's raw HTML (saved for provenance) and extracts the main
article text with a dependency-free, stdlib-only HTML-to-text pass. Writes:
  documents/raw/<id>-<slug>.html   raw downloaded HTML (the raw source document)
  documents/<id>-<slug>.txt        extracted, human-readable plain text
  documents/sources.json           manifest: filename -> {title, url, source, type, ...}

Why stdlib instead of trafilatura/bs4: this environment could not reliably pip-install
those, so extraction uses only Python's html.parser. It restricts to <article>/<main>
content when present to drop site nav/footers; Milestone 3's pipeline does the final
cleaning + normalization before chunking.

Reddit is intentionally absent: it blocks automated fetching (HTTP 403 / hard block),
so the corpus leans on The Technique (GT's student paper), a GT fan blog, a student-run
wiki, Niche student reviews, and local food guides instead.

Run:  ./.venv/bin/python scripts/collect_documents.py
"""
from __future__ import annotations

import json
import re
import time
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "documents"
RAW = DOCS / "raw"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# id, slug, title, source (publication), type (perspective), url
SOURCES = [
    (1, "technique-on-campus-dining-layout",
     "A full layout of on-campus dining at Tech",
     "The Technique (GT student newspaper)", "student newspaper",
     "https://nique.net/life/2023/08/25/a-full-layout-of-on-campus-dining-at-tech/"),
    (2, "technique-inside-look-dining-halls",
     "An inside look at Tech's Dining Halls and Services",
     "The Technique (GT student newspaper)", "student newspaper",
     "https://nique.net/life/2014/02/06/an-inside-look-at-techs-dining-halls-and-services/"),
    (3, "technique-tech-dining-rebrands",
     "Tech Dining rebrands, but does not improve",
     "The Technique (GT student newspaper)", "student newspaper (opinion)",
     "https://nique.net/opinions/2017/10/20/tech-dining-rebrands-but-does-not-improve/"),
    (4, "technique-meal-swipes",
     "Meal swipes in Tech Dining",
     "The Technique (GT student newspaper)", "student newspaper (opinion)",
     "https://nique.net/opinions/2023/02/19/meal-swipes-in-tech-dining/"),
    (5, "technique-late-night-dining",
     "Late night dining",
     "The Technique (GT student newspaper)", "student newspaper (opinion)",
     "https://nique.net/opinions/2012/03/02/late-night-dining/"),
    (6, "technique-extended-dining-hours",
     "Institute extends on-campus dining hours",
     "The Technique (GT student newspaper)", "student newspaper (news)",
     "https://nique.net/news/2021/10/29/institute-extends-on-campus-dining-hours/"),
    (7, "rumbleseat-dining-power-rankings",
     "Bye Week Power Rankings: Tech Dining Experiences",
     "From The Rumble Seat (GT fan blog, SB Nation)", "student/fan blog (opinion)",
     "https://www.fromtherumbleseat.com/2019/9/20/20874335/bye-week-power-rankings-tech-dining-experiences-georgia-tech-food-campus-services-chick-fil-a"),
    (8, "gtae-food-around-campus",
     "Food Around Campus",
     "GTAE Aero Maker Space Wiki (student-run)", "student wiki",
     "https://gtae.gitbook.io/ams/miscellaneous/food-around-campus"),
    (9, "infatuation-where-to-eat-near-gt",
     "Where To Eat Near Georgia Tech",
     "The Infatuation", "food guide",
     "https://www.theinfatuation.com/atlanta/guides/where-to-eat-near-georgia-tech"),
    (10, "rambler-top-restaurants-near-campus",
     "Top Restaurants Near Georgia Tech in Atlanta Midtown",
     "Rambler Atlanta (local student-housing blog)", "local guide/blog",
     "https://rambleratlanta.com/resources/top-restaurants-near-campus/"),
    (11, "rambler-meal-plans-guide",
     "Ultimate Guide to Georgia Tech Meal Plans",
     "Rambler Atlanta (local student-housing blog)", "local guide/blog",
     "https://rambleratlanta.com/resources/guide-gt-meal-plans/"),
    (12, "prked-meal-plans-guide",
     "Georgia Tech Meal Plans: The Ultimate Student Guide",
     "PRKED (student services blog)", "local guide/blog",
     "https://prked.com/post/georgia-tech-meal-plans-the-ultimate-student-guide"),
    (13, "niche-campus-life-food",
     "Georgia Tech Campus Life — Real Student Opinions (Food)",
     "Niche", "student reviews (aggregator)",
     "https://www.niche.com/colleges/georgia-institute-of-technology/campus-life/"),
    (14, "gtdining-dining-halls",
     "Dining Halls — Tech Dining",
     "Georgia Tech Dining (official)", "official",
     "https://dining.gatech.edu/dining-locations/dining-halls"),
]

SKIP_TAGS = {"script", "style", "noscript", "svg", "form", "button",
             "iframe", "template", "head", "nav", "aside"}
BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "li",
              "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "br",
              "blockquote", "figcaption", "pre", "td", "th"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        elif tag == "br":
            self.parts.append("\n")
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip > 0:
            self.skip -= 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.skip == 0:
            self.parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self.parts)
        lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in raw.split("\n")]
        lines = [ln for ln in lines if ln]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def main_region(html_doc: str) -> str:
    """Prefer the first sizable <article> or <main>; else <body>; else whole doc."""
    for tag in ("article", "main"):
        m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", html_doc, re.S | re.I)
        if m and len(m.group(1)) > 800:
            return m.group(1)
    m = re.search(r"<body\b[^>]*>(.*?)</body>", html_doc, re.S | re.I)
    return m.group(1) if m else html_doc


def extract_text(html_doc: str) -> str:
    p = TextExtractor()
    p.feed(main_region(html_doc))
    return p.get_text()


def fetch(url: str) -> tuple[int, str]:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    return r.status_code, r.text


def fetch_wayback(orig_url: str) -> tuple[str, str] | tuple[None, None]:
    """Fall back to the Internet Archive for pages that block bots or are now
    JS-only shells (e.g. nique.net migrated to a SPA and dropped old articles).
    Returns (raw_html_of_latest_200_snapshot, 'wayback:<timestamp>')."""
    bare = re.sub(r"^https?://", "", orig_url)
    cdx = (f"http://web.archive.org/cdx/search/cdx?url={bare}"
           "&output=json&filter=statuscode:200&collapse=digest&limit=10")
    for _ in range(2):
        try:
            rows = requests.get(cdx, headers={"User-Agent": UA}, timeout=60).json()
            break
        except Exception:  # noqa: BLE001
            rows = []
    if len(rows) <= 1:
        return None, None
    ts = rows[-1][1]  # latest snapshot
    snap = f"http://web.archive.org/web/{ts}id_/{orig_url}"
    try:
        r = requests.get(snap, headers={"User-Agent": UA}, timeout=60)
        if r.status_code == 200 and r.text:
            return r.text, f"wayback:{ts}"
    except Exception:  # noqa: BLE001
        pass
    return None, None


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = []
    print(f"{'id':>3}  {'status':<8} {'http':>5} {'method':<12} {'text chars':>10}  title")
    print("-" * 96)

    for sid, slug, title, source, dtype, url in SOURCES:
        base = f"{sid:02d}-{slug}"
        status, http, method, html_doc, text = "FAIL", "-", "-", "", ""

        # 1) direct fetch
        try:
            code, html_doc = fetch(url)
            http = code
            if code == 200 and html_doc:
                text = extract_text(html_doc)
                method = "direct"
        except Exception as e:  # noqa: BLE001
            http = f"ERR:{type(e).__name__}"

        # 2) Wayback fallback when direct is blocked or a JS-only/empty shell
        if len(text) < 400:
            wb_html, wb_meta = fetch_wayback(url)
            if wb_html:
                wb_text = extract_text(wb_html)
                if len(wb_text) >= 400:
                    html_doc, text, method = wb_html, wb_text, wb_meta

        n_chars = len(text)
        if n_chars >= 400:
            (RAW / f"{base}.html").write_text(html_doc, encoding="utf-8")
            (DOCS / f"{base}.txt").write_text(text, encoding="utf-8")
            status = "OK"
            manifest.append({
                "id": sid,
                "file": f"{base}.txt",
                "raw_html": f"raw/{base}.html",
                "title": title,
                "source": source,
                "type": dtype,
                "url": url,
                "retrieved_via": method,
                "chars": n_chars,
                "fetched": date.today().isoformat(),
            })
        elif http == 200 or method != "-":
            status = "THIN"
        print(f"{sid:>3}  {status:<8} {str(http):>5} {method:<12} {n_chars:>10}  {title[:44]}")
        time.sleep(1.0)  # be polite

    (DOCS / "sources.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("-" * 92)
    print(f"Collected {len(manifest)} documents -> {DOCS}")
    print(f"Manifest  -> {DOCS / 'sources.json'}")


if __name__ == "__main__":
    main()
