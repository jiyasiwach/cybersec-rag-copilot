"""POST /api/chat -> Server-Sent Events: guardrail -> sources -> token* -> done."""
import json
import logging
from typing import Iterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.guardrail import guard
from app.limits import limiter
from app.metrics import Timer, est_cost_usd
from app.rag.generator import new_result, stream_answer
from app.rag.retriever import Mode, get_retriever

log = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)  # guardrail enforces the 1000 limit with a clear verdict
    mode: Mode = "hybrid"


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def chat_events(req: ChatRequest) -> Iterator[str]:
    timer = Timer()
    question = req.question.strip()

    verdict = guard.check(question)
    timer.mark("guardrail")
    yield sse("guardrail", verdict.as_dict())
    if verdict.blocked:
        yield sse("done", {"retrieval_ms": 0, "generation_ms": 0, "total_ms": timer.total_ms(),
                           "prompt_tokens": 0, "completion_tokens": 0, "est_cost_usd": 0.0})
        return

    try:
        hits = get_retriever().search(question, req.mode, settings.top_k)
        timer.mark("retrieval")
        yield sse("sources", [{**h.chunk.__dict__, "n": h.rank, "score": h.score} for h in hits])

        result = new_result()
        for delta in stream_answer(question, hits, result):
            yield sse("token", delta)
        timer.mark("generation")

        u = result.usage
        yield sse("done", {
            "retrieval_ms": timer.phases["retrieval"], "generation_ms": timer.phases["generation"],
            "total_ms": timer.total_ms(), "prompt_tokens": u.prompt_tokens,
            "completion_tokens": u.completion_tokens, "est_cost_usd": est_cost_usd(u.prompt_tokens, u.completion_tokens),
        })
    except Exception:  # noqa: BLE001 - surface to the client, log the traceback server-side
        log.exception("chat failed")
        yield sse("error", {"message": "The assistant hit an error. Please retry."})


@router.post("/api/chat")
@limiter.limit(settings.rate_limit_chat)   # 10/minute per IP
def chat(request: Request, req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(chat_events(req), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
