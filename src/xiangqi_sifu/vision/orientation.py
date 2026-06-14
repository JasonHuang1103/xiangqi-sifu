from __future__ import annotations

from collections.abc import Mapping


def resolve_orientation(pieces: Mapping[str, str]) -> str:
    red_king = _find_piece(pieces, "K")
    black_king = _find_piece(pieces, "k")
    if red_king is None or black_king is None:
        return "unknown"
    red_rank = int(red_king[1])
    black_rank = int(black_king[1])
    if red_rank < black_rank:
        return "red_bottom"
    if red_rank > black_rank:
        return "red_top"
    return "unknown"


def _find_piece(pieces: Mapping[str, str], target: str) -> str | None:
    for square, piece in pieces.items():
        if piece == target:
            return square
    return None
