"""Layer 1: fast, free pattern checks. Returns a risk score in [0, 1] plus the rules that fired."""
import re
from dataclasses import dataclass, field

# (name, pattern, weight). Weights are additive and capped at 1.0.
RULES: list[tuple[str, re.Pattern[str], float]] = [
    ("ignore_instructions", re.compile(r"\b(ignore|disregard|forget)\b.{0,40}\b(previous|prior|above|earlier|all)\b.{0,20}\b(instructions?|rules?|prompts?)", re.I | re.S), 0.9),
    ("role_override", re.compile(r"\byou are now\b|\bfrom now on you\b|\bact as (?:an? )?(?:unrestricted|unfiltered|dan\b)|\bpretend (?:to be|you are)\b", re.I), 0.7),
    ("system_prompt", re.compile(r"\bsystem prompt\b|\binitial prompt\b|\bhidden (?:prompt|instructions)\b", re.I), 0.6),
    ("reveal_instructions", re.compile(r"\b(reveal|show|print|repeat|output|leak)\b.{0,30}\b(your )?(instructions|rules|prompt|configuration)\b", re.I | re.S), 0.7),
    ("developer_mode", re.compile(r"\bdeveloper mode\b|\bjailbreak\b|\bdo anything now\b|\bgod mode\b", re.I), 0.8),
    ("override_markers", re.compile(r"<\|?(?:im_start|system|endoftext)\|?>|\[\s*system\s*\]|^\s*system\s*:", re.I | re.M), 0.8),
    ("base64_blob", re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{60,}={0,2}(?![A-Za-z0-9+/])"), 0.6),
    ("too_long", re.compile(r"^[\s\S]{1001,}$"), 1.0),
]


@dataclass
class HeuristicResult:
    score: float
    matched: list[str] = field(default_factory=list)


def check(text: str) -> HeuristicResult:
    score = 0.0
    matched: list[str] = []
    for name, pattern, weight in RULES:
        if pattern.search(text):
            matched.append(name)
            score += weight
    return HeuristicResult(min(score, 1.0), matched)
