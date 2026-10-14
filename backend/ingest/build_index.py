"""Embed chunks.jsonl into ChromaDB and build the BM25 index.

    python -m ingest.build_index

Idempotent: the Chroma collection is dropped and rebuilt, the BM25 pickle overwritten.
Prints chunk count and the embedding cost estimate.
"""
import json
import pickle
import sys
import time

import chromadb
import tiktoken
from openai import OpenAI
from rank_bm25 import BM25Okapi

from app.config import settings
from app.rag.tokenize import tokenize

COLLECTION = "cybersec"
BATCH = 100
enc = tiktoken.get_encoding("cl100k_base")


def load_chunks() -> list[dict]:
    path = settings.chunks_path
    if not path.is_file():
        sys.exit(f"{path} not found — run `python -m ingest.process` first.")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_chroma(chunks: list[dict], client: OpenAI) -> int:
    """Embed in batches and upsert into a fresh collection. Returns tokens embedded."""
    db = chromadb.PersistentClient(path=str(settings.chroma_path))
    if COLLECTION in [c.name for c in db.list_collections()]:
        db.delete_collection(COLLECTION)
    col = db.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    total_tokens = 0
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start : start + BATCH]
        texts = [c["text"] for c in batch]
        total_tokens += sum(len(enc.encode(t)) for t in texts)
        resp = client.embeddings.create(model=settings.embedding_model, input=texts)
        col.add(
            ids=[c["chunk_id"] for c in batch],
            embeddings=[d.embedding for d in resp.data],
            documents=texts,
            metadatas=[{k: c[k] for k in ("source", "doc_id", "title", "url")} for c in batch],
        )
        done = min(start + BATCH, len(chunks))
        print(f"\r  embedded {done}/{len(chunks)}", end="", flush=True)
    print()
    return total_tokens


def build_bm25(chunks: list[dict]) -> None:
    bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
    settings.bm25_path.parent.mkdir(parents=True, exist_ok=True)
    with settings.bm25_path.open("wb") as f:
        pickle.dump({"bm25": bm25, "chunk_ids": [c["chunk_id"] for c in chunks]}, f)


def main() -> None:
    if not settings.openai_api_key:
        sys.exit("OPENAI_API_KEY is not set — copy .env.example to .env and fill it in.")
    chunks = load_chunks()
    print(f"{len(chunks)} chunks from {settings.chunks_path.name}")

    t0 = time.time()
    print(f"ChromaDB -> {settings.chroma_path}  (model {settings.embedding_model})")
    tokens = build_chroma(chunks, OpenAI(api_key=settings.openai_api_key))
    print("BM25     ->", settings.bm25_path)
    build_bm25(chunks)

    cost = tokens / 1_000_000 * settings.price_embedding_per_1m
    print(f"\ndone in {time.time() - t0:.0f}s: {len(chunks)} chunks, {tokens:,} tokens embedded, est. cost ${cost:.4f}")


if __name__ == "__main__":
    main()
