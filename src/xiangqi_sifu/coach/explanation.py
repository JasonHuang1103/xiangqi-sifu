from __future__ import annotations

from xiangqi_sifu.coach.mistake_detector import Mistake


def explain_mistake(mistake: Mistake) -> str:
    return (
        "Likely reason: the move caused a large engine evaluation loss. "
        "Phase 1 does not infer a deep strategic theme yet."
    )
