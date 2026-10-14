"""Latency timers, token counting and cost estimate."""
import time
from dataclasses import dataclass, field

import tiktoken

from app.config import settings

_enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def est_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    return round(
        prompt_tokens / 1e6 * settings.price_input_per_1m + completion_tokens / 1e6 * settings.price_output_per_1m, 6
    )


@dataclass
class Timer:
    """Records named phases; call mark('retrieval') when a phase ends."""
    start: float = field(default_factory=time.perf_counter)
    last: float = field(default_factory=time.perf_counter)
    phases: dict[str, int] = field(default_factory=dict)

    def mark(self, name: str) -> None:
        now = time.perf_counter()
        self.phases[name] = round((now - self.last) * 1000)
        self.last = now

    def total_ms(self) -> int:
        return round((time.perf_counter() - self.start) * 1000)
