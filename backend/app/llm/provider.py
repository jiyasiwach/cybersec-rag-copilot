"""Minimal provider interface so another vendor (e.g. Anthropic) can be added later."""
from dataclasses import dataclass
from typing import Iterator, Protocol


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class StreamResult:
    """Filled in as the stream is consumed; `usage` is final once the iterator is exhausted."""
    usage: Usage


class LLMProvider(Protocol):
    def stream(self, system: str, user: str, result: StreamResult) -> Iterator[str]:
        """Yield text deltas. Must set result.usage when the stream ends."""
        ...

    def complete_json(self, system: str, user: str, max_tokens: int = 200) -> dict:
        """One non-streamed call that must return a JSON object."""
        ...
