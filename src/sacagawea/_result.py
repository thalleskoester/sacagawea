"""Evaluation result contracts."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FinalResult:
    """Successful interpretation output."""

    result: list[dict]
    elapsed: float
