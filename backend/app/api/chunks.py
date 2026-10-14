from fastapi import APIRouter, HTTPException

from app.rag.retriever import load_chunks

router = APIRouter()


@router.get("/api/chunks/{chunk_id}")
def get_chunk(chunk_id: str) -> dict:
    """Full chunk + metadata behind a citation."""
    chunk = load_chunks().get(chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return chunk.__dict__
