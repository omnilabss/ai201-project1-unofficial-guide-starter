"""
The Unofficial Guide — GT campus dining. Gradio web UI (Milestone 5).

Run:  python app.py   →  open http://localhost:7860

Type a question, get an answer drawn only from the retrieved student sources,
with the sources it cited listed underneath. The first question takes a few
seconds while the embedding model loads; after that it's fast.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import gradio as gr  # noqa: E402
from answer import ask  # noqa: E402

EXAMPLES = [
    "What are Georgia Tech's three dining halls, and where are they?",
    "Is the Georgia Tech meal plan worth it?",
    "Where can I get coffee on campus near the CULC?",
    "What food is open late near campus?",
    "What do students call the West Village dining hall?",
]


def handle_query(question: str):
    if not question or not question.strip():
        return "Type a question above and press Ask.", ""
    result = ask(question.strip())
    if result["sources"]:
        sources = "\n".join(
            f"• {s['title']} ({s['source']})\n  {s['url']}"
            for s in result["sources"]
        )
    else:
        sources = "(No sources — the guide doesn't cover this question.)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide — GT Dining") as demo:
    gr.Markdown(
        "# The Unofficial Guide — Georgia Tech Campus Dining\n"
        "Ask anything about GT dining halls, meal plans, coffee, late-night food, "
        "or nearby spots. Answers come **only** from real student sources "
        "(the Technique, student wikis, reviews) and cite where they came from."
    )
    inp = gr.Textbox(label="Your question",
                     placeholder="e.g. Is the meal plan worth it?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=5)
    gr.Examples(EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
