from __future__ import annotations

import math

from xiangqi_sifu.analysis.models import MoveImpact


def estimated_red_win_rate(score_cp: int | None) -> float | None:
    if score_cp is None:
        return None
    estimate = 1.0 / (1.0 + math.exp(-score_cp / 240.0))
    return round(min(0.99, max(0.01, estimate)), 4)


def move_impact(*, before_red_cp: int, after_red_cp: int, side: str) -> MoveImpact:
    if side == "red":
        score_change = after_red_cp - before_red_cp
    elif side == "black":
        score_change = before_red_cp - after_red_cp
    else:
        raise ValueError(f"Unsupported side: {side!r}")
    loss = max(0, -score_change)
    return MoveImpact(
        score_change_cp=score_change,
        mover_loss_cp=loss,
        classification=_classification(loss),
    )


def _classification(loss_cp: int) -> str:
    if loss_cp >= 300:
        return "blunder"
    if loss_cp >= 150:
        return "mistake"
    if loss_cp >= 80:
        return "inaccuracy"
    if loss_cp > 0:
        return "good"
    return "best"
