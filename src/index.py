"""
Milestone 4 — embedding + retrieval for The Unofficial Guide (GT campus dining).

Embeds the chunks from chunks.json with all-MiniLM-L6-v2 and stores them in a
persistent ChromaDB collection (cosine distance) with their source metadata.
`search()` embeds a query with the same model and returns the top-k nearest
chunks plus distances and source info.

Run `python src/index.py` to (re)build the index and run a retrieval-only smoke
test against the five planning.md eval questions — no LLM involved yet, because
most RAG failures are retrieval failures and they're cheaper to catch here.
"""
from __future__ import annotations

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "chunks.json"
DB = ROOT / "chroma_db"
COLLECTION = "gt_dining"
MODEL_NAME = "all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_collection(create: bool = False):
    client = chromadb.PersistentClient(path=str(DB))
    if create:
        try:
            client.delete_collection(COLLECTION)
        except Exception:  # noqa: BLE001 — fine if it doesn't exist yet
            pass
        # cosine space so distances live in ~[0, 2] and ~<0.5 means "relevant"
        return client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    return client.get_collection(COLLECTION)


def build_index() -> int:
    chunks = json.loads(CHUNKS.read_text(encoding="utf-8"))
    texts = [c["text"] for c in chunks]
    embeddings = get_model().encode(
        texts, batch_size=64, convert_to_numpy=True, show_progress_bar=False)
    col = get_collection(create=True)
    col.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[c["metadata"] for c in chunks],
    )
    return col.count()


def search(query: str, k: int = 5, max_distance: float | None = None) -> list[dict]:
    """Top-k chunks for a query. max_distance drops weak matches (used by the
    generation step to abstain when nothing relevant is retrieved)."""
    q_emb = get_model().encode([query], convert_to_numpy=True)[0].tolist()
    res = get_collection().query(query_embeddings=[q_emb], n_results=k)
    hits = []
    for cid, doc, meta, dist in zip(
        res["ids"][0], res["documents"][0],
        res["metadatas"][0], res["distances"][0],
    ):
        if max_distance is not None and dist > max_distance:
            continue
        hits.append({"id": cid, "text": doc, "metadata": meta, "distance": dist})
    return hits


# ---------------------------------------------------------------------------
# Retrieval-only acceptance test (planning.md eval questions)
# ---------------------------------------------------------------------------

EVAL = [
    ("What are Georgia Tech's three official dining halls, and which campus side is each on?", {1, 8, 14}),
    ("What do students call the West Village dining hall?", {1, 8}),
    ("Where can I get coffee on campus near the CULC?", {1, 8}),
    ("Roughly how much does a Georgia Tech meal plan cost?", {11, 12, 13}),
    ("What are some late-night food options on or near campus?", {5, 8, 9}),
]


def smoke_test() -> None:
    passed = 0
    for i, (q, expected) in enumerate(EVAL, 1):
        hits = search(q, k=5)
        got = {h["metadata"]["doc_id"] for h in hits}
        hit_expected = got & expected
        ok = bool(hit_expected)
        passed += ok
        print(f"\nQ{i}: {q}")
        print(f"   expected docs {sorted(expected)} | got {sorted(got)} "
              f"| {'PASS' if ok else 'MISS'} (overlap {sorted(hit_expected)})")
        for h in hits:
            m = h["metadata"]
            snippet = " ".join(h["text"].split())[:110]
            print(f"   [{h['distance']:.3f}] doc{m['doc_id']:>2} {m['title'][:32]:<32} | {snippet}")
    print(f"\nRetrieval acceptance: {passed}/{len(EVAL)} questions hit an expected source doc.")


if __name__ == "__main__":
    n = build_index()
    print(f"Indexed {n} chunks into ChromaDB collection '{COLLECTION}' ({DB.name}/).")
    smoke_test()
