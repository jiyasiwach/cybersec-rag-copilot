"""Retrieval over the knowledge base: vector (ChromaDB), BM25 (rank_bm25) and hybrid (RRF).

All three modes return the same shape so the API, prompt builder and evals don't care which
one ran. Loaded once per process (see `get_retriever`).
"""
import json
import pickle
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import chromadb
from openai import OpenAI
from rank_bm25 import BM25Okapi

from app.config import settings
from app.rag.tokenize import tokenize

Mode = Literal["vector", "bm25", "hybrid"]
COLLECTION = "cybersec"
CANDIDATES = 20   # top-N pulled from each engine before fusion
RRF_K = 60

# IDs we boost to position 1 when they appear verbatim in the query.
ID_PATTERNS = [
    re.compile(r"\bT\d{4}(?:\.\d{3})?\b", re.I),      # T1059, T1059.001
    re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.I),        # CVE-2024-3400
    re.compile(r"\bA(?:0[1-9]|10)(?::2021)?\b", re.I),  # A03, A03:2021
]


@dataclass
class Chunk:
    chunk_id: str
    source: str
    doc_id: str
    title: str
    url: str
    text: str


@dataclass
class Hit:
    chunk: Chunk
    score: float   # mode-specific: cosine similarity, BM25 score, or RRF score
    rank: int      # 1-based final rank


def rrf(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    """Reciprocal Rank Fusion: score(id) = Σ 1 / (k + rank). Pure function, unit-tested."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    return scores


def ids_in_query(query: str) -> list[str]:
    """Normalised doc_ids mentioned in the query, e.g. ['T1059.001', 'A03:2021']."""
    found: list[str] = []
    for pat in ID_PATTERNS:
        for m in pat.findall(query):
            doc_id = m.upper()
            if doc_id.startswith("A") and ":2021" not in doc_id:
                doc_id += ":2021"
            found.append(doc_id)
    return found


@lru_cache(maxsize=1)
def load_chunks() -> dict[str, Chunk]:
    """chunk_id -> Chunk from chunks.jsonl. Needs no index, so /api/chunks works before build_index."""
    chunks: dict[str, Chunk] = {}
    for line in settings.chunks_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            c = Chunk(**json.loads(line))
            chunks[c.chunk_id] = c
    return chunks


class Retriever:
    def __init__(self) -> None:
        self.chunks = load_chunks()
        self.by_doc: dict[str, str] = {}   # doc_id -> first chunk_id
        for cid, c in self.chunks.items():
            self.by_doc.setdefault(c.doc_id.upper(), cid)

        with settings.bm25_path.open("rb") as f:
            blob = pickle.load(f)
        self.bm25: BM25Okapi = blob["bm25"]
        self.bm25_ids: list[str] = blob["chunk_ids"]

        self.collection = chromadb.PersistentClient(path=str(settings.chroma_path)).get_collection(COLLECTION)
        self.openai = OpenAI(api_key=settings.openai_api_key)

    # ---- engines: each returns ranked (chunk_id, score) ----

    def _vector(self, query: str, n: int) -> list[tuple[str, float]]:
        emb = self.openai.embeddings.create(model=settings.embedding_model, input=[query]).data[0].embedding
        res = self.collection.query(query_embeddings=[emb], n_results=n, include=["distances"])
        return [(cid, 1.0 - dist) for cid, dist in zip(res["ids"][0], res["distances"][0])]

    def _bm25(self, query: str, n: int) -> list[tuple[str, float]]:
        scores = self.bm25.get_scores(tokenize(query))
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        return [(self.bm25_ids[i], float(scores[i])) for i in top if scores[i] > 0]

    # ---- public ----

    def search(self, query: str, mode: Mode = "hybrid", k: int | None = None) -> list[Hit]:
        k = k or settings.top_k
        if mode == "vector":
            ranked = self._vector(query, CANDIDATES)
        elif mode == "bm25":
            ranked = self._bm25(query, CANDIDATES)
        else:
            vec = [cid for cid, _ in self._vector(query, CANDIDATES)]
            kw = [cid for cid, _ in self._bm25(query, CANDIDATES)]
            fused = rrf([vec, kw])
            ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)

        # exact-ID boost: a chunk whose doc_id is named in the query goes first
        boosted: list[tuple[str, float]] = []
        for doc_id in ids_in_query(query):
            cid = self.by_doc.get(doc_id)
            if cid and cid not in {b for b, _ in boosted}:
                boosted.append((cid, max((s for c, s in ranked if c == cid), default=0.0)))
        ranked = boosted + [(cid, s) for cid, s in ranked if cid not in {b for b, _ in boosted}]

        return [Hit(self.chunks[cid], round(score, 4), i + 1) for i, (cid, score) in enumerate(ranked[:k])]

    def get(self, chunk_id: str) -> Chunk | None:
        return self.chunks.get(chunk_id)


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever()
