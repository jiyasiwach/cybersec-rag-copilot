"""Settings loaded from backend/.env (see .env.example). Never hard-code secrets."""
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI
    openai_api_key: str = ""
    # Leave empty for api.openai.com. Set to https://openrouter.ai/api/v1 to use OpenRouter
    # (then prefix models with the vendor, e.g. openai/gpt-4.1-mini).
    openai_base_url: str | None = None
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4.1-mini"

    # Pricing, USD per 1M tokens
    price_input_per_1m: float = 0.40
    price_output_per_1m: float = 1.60
    price_embedding_per_1m: float = 0.02

    # Retrieval
    top_k: int = 5
    retrieval_mode: Literal["vector", "bm25", "hybrid"] = "hybrid"

    # Guardrail
    max_input_chars: int = 1000

    # Server
    frontend_origin: str = "http://localhost:5173"
    rate_limit_chat: str = "10/minute"

    # Paths (relative to backend/)
    chroma_dir: str = "chroma"
    chunks_file: str = "../data/processed/chunks.jsonl"
    bm25_file: str = "data/bm25.pkl"

    @property
    def chroma_path(self) -> Path:
        return BACKEND_DIR / self.chroma_dir

    @property
    def chunks_path(self) -> Path:
        return (BACKEND_DIR / self.chunks_file).resolve()

    @property
    def bm25_path(self) -> Path:
        return BACKEND_DIR / self.bm25_file


settings = Settings()
