from __future__ import annotations

from dataclasses import dataclass

from xiangqi_sifu.engine.analysis import Evaluation
from xiangqi_sifu.parsers.base import ParsedMove


@dataclass(frozen=True)
class MistakeThresholds:
    inaccuracy_cp: int = 80
    mistake_cp: int = 150
    blunder_cp: int = 300
    suppress_when_best_matches_played: bool = True


@dataclass(frozen=True)
class Mistake:
    ply: int
    move_number: int
    side: str
    played_move: str
    best_move: str | None
    severity: str
    eval_before_cp: int
    eval_after_cp: int
    eval_loss_cp: int


def detect_mistakes(
    moves: list[ParsedMove],
    evaluations: list[Evaluation],
    thresholds: MistakeThresholds | None = None,
) -> list[Mistake]:
    thresholds = thresholds or MistakeThresholds()
    mistakes: list[Mistake] = []
    for index, move in enumerate(moves):
        if index + 1 >= len(evaluations):
            break
        before = evaluations[index]
        after = evaluations[index + 1]
        if before.red_score_cp is None or after.red_score_cp is None:
            continue
        if (
            thresholds.suppress_when_best_matches_played
            and before.best_move is not None
            and before.best_move == move.uci
        ):
            continue

        loss = _eval_loss_for_side(move.side, before.red_score_cp, after.red_score_cp)
        severity = _severity(loss, thresholds)
        if severity is None:
            continue
        mistakes.append(
            Mistake(
                ply=index + 1,
                move_number=move.move_number,
                side=move.side,
                played_move=move.uci,
                best_move=before.best_move,
                severity=severity,
                eval_before_cp=before.red_score_cp,
                eval_after_cp=after.red_score_cp,
                eval_loss_cp=loss,
            )
        )
    return mistakes


def _eval_loss_for_side(side: str, before_red_cp: int, after_red_cp: int) -> int:
    if side == "red":
        return before_red_cp - after_red_cp
    if side == "black":
        return after_red_cp - before_red_cp
    raise ValueError(f"Unsupported side: {side!r}")


def _severity(loss_cp: int, thresholds: MistakeThresholds) -> str | None:
    if loss_cp >= thresholds.blunder_cp:
        return "blunder"
    if loss_cp >= thresholds.mistake_cp:
        return "mistake"
    if loss_cp >= thresholds.inaccuracy_cp:
        return "inaccuracy"
    return None
