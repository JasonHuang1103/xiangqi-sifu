from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    ply: int
    fen: str
    side_to_move: str
    move_uci: str | None = None
    move_iccs: str | None = None
