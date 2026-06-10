"""
Milestone 6 — evaluation harness for The Unofficial Guide (GT campus dining).

Runs the five planning.md test questions through the full system (retrieve →
grounded generate) and prints, for each: the question, the expected answer, the
system's answer, the sources it cited, and the retrieved (doc_id, distance) list.
Ends with a diagnostic for the meal-plan-cost question — where the price figures
actually rank — to support the failure-case analysis in the README.

Run:  python src/evaluate.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer import ask  # noqa: E402
from index import search  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

EVAL = [
    {"q": "What are Georgia Tech's three official dining halls, and which campus side is each on?",
     "expected": "Brittain and North Avenue on East Campus; West Village (\"Willage\") on West Campus. All all-you-can-eat."},
    {"q": "What do students call the West Village dining hall?",
     "expected": "\"Willage.\""},
    {"q": "Where can I get coffee on campus near the CULC?",
     "expected": "Kaldi's Coffee, 2nd floor of the CULC (also Gold & Bold, Sideways Cafe)."},
    {"q": "Roughly how much does a Georgia Tech meal plan cost?",
     "expected": "~$2,977/semester for first-year plans (per the guides); ~$4,840/year per Niche."},
    {"q": "What are some late-night food options on or near campus?",
     "expected": "The Missing T; WingZone & Starbucks at West Village stay open latest; Waffle House (24h) & Insomnia Cookies in Tech Square; Sublime Doughnuts (24/7)."},
]

PRICE_TOKENS = ("$2,977", "$2977", "2,977", "2977", "$4,840", "4,840")


def main() -> None:
    for i, item in enumerate(EVAL, 1):
        r = ask(item["q"])
        retrieved = [(h["metadata"]["doc_id"], round(h["distance"], 3)) for h in r["chunks"]]
        print("=" * 92)
        print(f"Q{i}: {item['q']}")
        print(f"EXPECTED : {item['expected']}")
        print(f"ANSWER   : {r['answer']}")
        print(f"CITED    : {[s['title'] for s in r['sources']]}")
        print(f"RETRIEVED: {retrieved}")

    print("\n" + "#" * 92)
    print("DIAGNOSTIC — meal-plan-cost question: where do the price figures rank?")
    hits = search("Roughly how much does a Georgia Tech meal plan cost?", k=12)
    for rank, h in enumerate(hits, 1):
        has_price = any(p in h["text"] for p in PRICE_TOKENS)
        snippet = " ".join(h["text"].split())[:64]
        print(f"  #{rank:>2} d={h['distance']:.3f} doc{h['metadata']['doc_id']:>2} "
              f"price={'YES' if has_price else ' no'} :: {snippet}")

    chunks = json.loads((ROOT / "chunks.json").read_text(encoding="utf-8"))
    price_chunks = [(c["id"], c["metadata"]["doc_id"])
                    for c in chunks if any(p in c["text"] for p in PRICE_TOKENS)]
    print(f"\nChunks in corpus containing a price figure: {price_chunks}")


if __name__ == "__main__":
    main()
