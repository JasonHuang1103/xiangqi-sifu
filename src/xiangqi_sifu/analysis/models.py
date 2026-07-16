from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EngineLine:
    multipv: int
    red_score_cp: int | None
    mate_score: int | None
    best_move: str | None
    pv: tuple[str, ...] = field(default_factory=tuple)
    depth: int | None = None
    nodes: int | None = None


@dataclass(frozen=True)
class MoveImpact:
    score_change_cp: int
    mover_loss_cp: int
    classification: str
