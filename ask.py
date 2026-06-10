"""
The Unofficial Guide — GT campus dining. Command-line interface (Milestone 5).

Two ways to use it:
  python ask.py "is the meal plan worth it?"   # one-shot
  python ask.py                                 # interactive: model loads once,
                                                # then ask as many questions as you like

The interactive mode is the one to demo: the embedding model loads on the first
question and stays warm, so follow-up questions answer immediately.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from answer import ask  # noqa: E402


def show(question: str) -> None:
    result = ask(question)
    print(f"\nAnswer:\n{result['answer']}")
    if result["sources"]:
        print("\nRetrieved from:")
        for s in result["sources"]:
            print(f"  • {s['title']} ({s['source']})")
            print(f"    {s['url']}")
    print("-" * 72)


def main() -> None:
    if len(sys.argv) > 1:
        show(" ".join(sys.argv[1:]))
        return
    print("The Unofficial Guide to Georgia Tech campus dining.")
    print("Ask a question (or type 'quit'). First answer takes a few seconds to load the model.")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in {"quit", "exit", "q"}:
            break
        show(q)


if __name__ == "__main__":
    main()
