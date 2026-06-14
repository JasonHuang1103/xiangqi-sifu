from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from xiangqi_sifu.vision.board_detector import ensure_image_path
from xiangqi_sifu.vision.grid_mapper import BoardRectangle
from xiangqi_sifu.vision.piece_classifier import LabelledBoard


@dataclass(frozen=True)
class TemplateMatch:
    piece: str | None
    confidence: float


class TemplatePieceRecognizer:
    def __init__(self, template_dir: str | Path) -> None:
        self.template_dir = Path(template_dir)
        manifest_path = self.template_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        templates = manifest.get("templates")
        if not isinstance(templates, dict) or not templates:
            raise ValueError("Template manifest must contain a non-empty templates object")
        self.templates = {
            str(piece): Image.open(self.template_dir / str(filename)).convert("RGB")
            for piece, filename in templates.items()
        }

    def classify(self, crop: Image.Image, *, threshold: float) -> TemplateMatch:
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
            return TemplateMatch(piece=None, confidence=best_score)
        return TemplateMatch(piece=best_piece, confidence=best_score)


def recognize_board_from_image(
    image_path: str | Path,
    *,
    template_dir: str | Path,
    board_rect: BoardRectangle,
    active_color: str,
    threshold: float = 0.92,
    crop_scale: float = 0.8,
) -> LabelledBoard:
    ensure_image_path(image_path)
    image = Image.open(image_path).convert("RGB")
    recognizer = TemplatePieceRecognizer(template_dir)
    crop_size = min(board_rect.width / 8, board_rect.height / 9) * crop_scale
    pieces: dict[str, str] = {}
    confidence: dict[str, float] = {}
    for point in board_rect.grid_points():
        crop = _crop_centered(image, point.x, point.y, crop_size)
        match = recognizer.classify(crop, threshold=threshold)
        if match.piece is not None:
            pieces[point.square] = match.piece
            confidence[point.square] = match.confidence
    return LabelledBoard(
        pieces=pieces,
        active_color=active_color,
        confidence_by_square=confidence,
    )


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
