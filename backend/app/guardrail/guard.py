"""Guardrail entrypoint, run before retrieval.

Decision:
  heuristic score >= BLOCK_THRESHOLD (0.6)  -> block as injection, no LLM call
  heuristic score == 0 and looks like a plain question -> still run the classifier (catches
      paraphrased injections and off-topic questions the regexes can't see)
  otherwise                                  -> classifier decides
Threshold rationale: a single strong rule (ignore-instructions 0.9, jailbreak 0.8,
override markers 0.8) blocks outright; weaker single rules (system_prompt 0.6, base64 0.6)
sit exactly at the line so they block too, while the classifier handles everything else.
"""
import logging
from dataclasses import asdict, dataclass
from typing import Literal

from app.config import settings
from app.guardrail import classifier, heuristics

log = logging.getLogger(__name__)
Verdict = Literal["safe", "injection", "off_topic"]
BLOCK_THRESHOLD = 0.6


@dataclass
class GuardResult:
    blocked: bool
    verdict: Verdict
    reason: str
    layer: Literal["heuristic", "classifier"] | None
    risk_score: float

    def as_dict(self) -> dict:
        return asdict(self)


def check(question: str, use_classifier: bool = True) -> GuardResult:
    if len(question) > settings.max_input_chars:
        return GuardResult(True, "injection", f"Input exceeds {settings.max_input_chars} characters.", "heuristic", 1.0)

    h = heuristics.check(question)
    if h.score >= BLOCK_THRESHOLD:
        return GuardResult(True, "injection", "Matched rules: " + ", ".join(h.matched), "heuristic", h.score)

    if not use_classifier:
        return GuardResult(False, "safe", "Heuristics passed (classifier disabled).", "heuristic", h.score)

    try:
        c = classifier.classify(question)
    except Exception:  # noqa: BLE001 - fail open on classifier errors, but say so
        log.exception("classifier failed")
        return GuardResult(False, "safe", "Heuristics passed; classifier unavailable.", "heuristic", h.score)

    if c.verdict == "safe":
        return GuardResult(False, "safe", c.reason or "Classified as a cybersecurity question.", "classifier", h.score)
    return GuardResult(True, c.verdict, c.reason, "classifier", max(h.score, 0.5))
