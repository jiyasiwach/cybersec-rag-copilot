"""Turn (question, hits) into a streamed answer with usage."""
from typing import Iterator

from app.llm.openai_provider import get_provider
from app.llm.provider import StreamResult, Usage
from app.rag.prompt import SYSTEM_PROMPT, build_user_message
from app.rag.retriever import Hit


def stream_answer(question: str, hits: list[Hit], result: StreamResult) -> Iterator[str]:
    return get_provider().stream(SYSTEM_PROMPT, build_user_message(question, hits), result)


def new_result() -> StreamResult:
    return StreamResult(usage=Usage())
