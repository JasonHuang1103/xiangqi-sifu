from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

FILES = "abcdefghi"
VALID_PIECES = set("rnbakcpRNBAKCP")


@dataclass(frozen=True)
class BoardRectangle:
    x: float
    y: float
    width: float
    height: float

    @classmethod
    def parse(cls, value: str) -> "BoardRectangle":
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 4:
            raise ValueError("Board rectangle must use x,y,width,height format")
        return cls(*(float(part) for part in parts))

    def grid_points(self) -> list[tuple[str, float, float]]:
        file_step = self.width / 8
        rank_step = self.height / 9
        points: list[tuple[str, float, float]] = []
        for row_index, rank in enumerate(range(9, -1, -1)):
            for file_index, file_name in enumerate(FILES):
                points.append(
                    (
                        f"{file_name}{rank}",
                        self.x + file_step * file_index,
                        self.y + rank_step * row_index,
                    )
                )
        return points


class TemplateRecognizer:
    def __init__(self, template_dir: str | Path) -> None:
        self.template_dir = Path(template_dir)
        manifest = json.loads((self.template_dir / "manifest.json").read_text(encoding="utf-8"))
        templates = manifest.get("templates")
        if not isinstance(templates, dict) or not templates:
            raise ValueError("Template manifest must contain a non-empty templates object")
        self.templates = {
            str(piece): Image.open(self.template_dir / str(filename)).convert("RGB")
            for piece, filename in templates.items()
        }

    def classify(self, crop: Image.Image, *, threshold: float) -> tuple[str | None, float]:
        crop_image = crop.convert("RGB")
        crop_array = _image_array(crop_image)
        best_piece: str | None = None
        best_score = -1.0
        for piece, template in self.templates.items():
            resized = template.resize(crop_image.size, _resampling_filter())
            score = 1.0 - float(np.mean(np.abs(crop_array - _image_array(resized)))) / 255.0
            if score > best_score:
                best_piece = piece
                best_score = score
        if best_score < threshold:
            return None, best_score
        return best_piece, best_score


def screenshot_to_fen(
    image_path: str | Path,
    *,
    template_dir: str | Path,
    board_rect: BoardRectangle,
    active_color: str = "w",
    threshold: float = 0.92,
    crop_scale: float = 0.8,
) -> tuple[str, float, int]:
    image = Image.open(image_path).convert("RGB")
    recognizer = TemplateRecognizer(template_dir)
    crop_size = min(board_rect.width / 8, board_rect.height / 9) * crop_scale
    pieces: dict[str, str] = {}
    confidences: list[float] = []
    for square, x, y in board_rect.grid_points():
        crop = _crop_centered(image, x, y, crop_size)
        piece, score = recognizer.classify(crop, threshold=threshold)
        if piece is not None:
            pieces[square] = piece
            confidences.append(score)
    fen = fen_from_piece_map(pieces, active_color=active_color)
    return fen, min(confidences) if confidences else 0.0, len(pieces)


def fen_from_piece_map(pieces: dict[str, str], *, active_color: str) -> str:
    rows: list[str] = []
    for rank in range(9, -1, -1):
        empty = 0
        encoded: list[str] = []
        for file_name in FILES:
            piece = pieces.get(f"{file_name}{rank}")
            if piece is None:
                empty += 1
                continue
            if piece not in VALID_PIECES:
                raise ValueError(f"Unsupported Xiangqi FEN piece: {piece!r}")
            if empty:
                encoded.append(str(empty))
                empty = 0
            encoded.append(piece)
        if empty:
            encoded.append(str(empty))
        rows.append("".join(encoded))
    fen = f"{'/'.join(rows)} {active_color} - - 0 1"
    validate_fen(fen)
    return fen


def validate_fen(fen: str) -> None:
    fields = fen.split()
    if len(fields) != 6:
        raise ValueError(f"Expected 6-field FEN: {fen!r}")
    rows = fields[0].split("/")
    if len(rows) != 10:
        raise ValueError(f"Expected 10 board rows: {fen!r}")
    for row in rows:
        columns = 0
        for char in row:
            columns += int(char) if char.isdigit() else 1
        if columns != 9:
            raise ValueError(f"Expected 9 files in row {row!r}")


def _crop_centered(image: Image.Image, x: float, y: float, size: float) -> Image.Image:
    half = size / 2
    return image.crop(
        (
            int(round(x - half)),
            int(round(y - half)),
            int(round(x + half)),
            int(round(y + half)),
        )
    )


def _image_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image, dtype=np.float32)


def _resampling_filter() -> int:
    return getattr(Image, "Resampling", Image).BILINEAR
