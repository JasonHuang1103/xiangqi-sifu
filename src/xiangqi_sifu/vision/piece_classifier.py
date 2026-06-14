from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xiangqi_sifu.vision.fen_from_image import fen_from_piece_map


@dataclass(frozen=True)
class LabelledBoard:
    pieces: dict[str, str]
    active_color: str = "w"
    confidence_by_square: dict[str, float] | None = None

    @property
    def confidence(self) -> float:
        if not self.confidence_by_square:
            return 1.0
        return min(self.confidence_by_square.values())

    @property
    def uncertain_squares(self) -> list[str]:
        if not self.confidence_by_square:
            return []
        return sorted(square for square, score in self.confidence_by_square.items() if score < 0.75)

    def to_fen(self) -> str:
        return fen_from_piece_map(self.pieces, active_color=self.active_color)


def load_labelled_board(path: str | Path) -> LabelledBoard:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Label file must contain a JSON object")

    raw_pieces: Any = data.get("pieces", data)
    if not isinstance(raw_pieces, dict):
        raise ValueError("Label file must contain a pieces object")

    confidence = data.get("confidence")
    if confidence is not None and not isinstance(confidence, dict):
        raise ValueError("Label confidence must be an object when provided")

    return LabelledBoard(
        pieces={str(square): str(piece) for square, piece in raw_pieces.items()},
        active_color=str(data.get("active_color", "w")),
        confidence_by_square=(
            {str(square): float(score) for square, score in confidence.items()}
            if confidence is not None
            else None
        ),
    )
