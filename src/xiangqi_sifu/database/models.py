from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SavedAnalysis:
    game_id: int
    move_count: int
    evaluation_count: int
    mistake_count: int
