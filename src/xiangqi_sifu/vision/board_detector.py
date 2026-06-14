from __future__ import annotations

from pathlib import Path

from xiangqi_sifu.vision.grid_mapper import BoardRectangle


def ensure_image_path(path: str | Path) -> Path:
    image_path = Path(path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"Image path is not a file: {image_path}")
    return image_path


def manual_board_rectangle(value: str | None) -> BoardRectangle | None:
    if value is None:
        return None
    return BoardRectangle.parse(value)
