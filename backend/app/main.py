"""FastAPI entrypoint: CORS, rate limiting, routers."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import chat, chunks, eval as eval_api, health, search
from app.config import settings
from app.limits import limiter

app = FastAPI(title="CyberSec RAG Copilot", docs_url="/docs")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(chunks.router)
app.include_router(chat.router)
app.include_router(eval_api.router)
