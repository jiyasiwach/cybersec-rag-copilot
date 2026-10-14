from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "index_present": settings.chroma_path.is_dir() and settings.bm25_path.is_file(),
    }
