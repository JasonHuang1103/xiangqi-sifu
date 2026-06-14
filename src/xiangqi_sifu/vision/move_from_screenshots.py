from __future__ import annotations

from dataclasses import dataclass

from xiangqi_sifu.board.move import uci_to_iccs
from xiangqi_sifu.vision.fen_from_image import fen_to_piece_map


@dataclass(frozen=True)
class MoveInference:
    move_uci: str
    move_iccs: str
    confidence: float
    changed_squares: tuple[str, ...]


def infer_move_from_fens(before_fen: str, after_fen: str) -> MoveInference:
    return infer_move_from_piece_maps(fen_to_piece_map(before_fen), fen_to_piece_map(after_fen))


def infer_move_from_piece_maps(
    before: dict[str, str],
    after: dict[str, str],
) -> MoveInference:
    changed = sorted(
        square
        for square in set(before) | set(after)
        if before.get(square) != after.get(square)
    )
    if len(changed) != 2:
        raise ValueError(f"Expected exactly two changed squares, got {changed}")

    source_candidates = [square for square in changed if square in before and before.get(square) != after.get(square)]
    destination_candidates = [
        square
        for square in changed
        if square in after and after.get(square) != before.get(square)
    ]
    for source in source_candidates:
        moved_piece = before[source]
        for destination in destination_candidates:
            if after[destination] == moved_piece and after.get(source) is None:
                move_uci = f"{source}{destination}"
                return MoveInference(
                    move_uci=move_uci,
                    move_iccs=uci_to_iccs(move_uci),
                    confidence=1.0,
                    changed_squares=tuple(changed),
                )

    raise ValueError(f"Could not infer a single move from changed squares: {changed}")
