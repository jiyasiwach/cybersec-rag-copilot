from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.rag.retriever import Mode, get_retriever

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    mode: Mode = "hybrid"
    k: int = Field(default=5, ge=1, le=20)


class SearchHit(BaseModel):
    chunk_id: str
    source: str
    doc_id: str
    title: str
    url: str
    text: str
    score: float
    rank: int


@router.post("/api/search", response_model=list[SearchHit])
def search(req: SearchRequest) -> list[SearchHit]:
    """Ranked chunks with scores — used by the Eval page and for debugging retrieval."""
    hits = get_retriever().search(req.query, req.mode, req.k)
    return [SearchHit(**h.chunk.__dict__, score=h.score, rank=h.rank) for h in hits]
