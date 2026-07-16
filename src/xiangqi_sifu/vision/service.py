from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Mapping

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from xiangqi_sifu.vision.fen_from_image import fen_from_piece_map, fen_to_piece_map
from xiangqi_sifu.vision.grid_mapper import BoardRectangle
from xiangqi_sifu.vision.orientation import resolve_orientation

WOOD = (217, 184, 115)
GRID = (102, 75, 40)
PAPER = (242, 234, 216)
PIECE_FACE = (246, 232, 201)
RED = (164, 56, 47)
BLACK = (38, 35, 30)

PIECE_GLYPHS = {
    "R": "俥",
    "N": "傌",
    "B": "相",
    "A": "仕",
    "K": "帥",
    "C": "炮",
    "P": "兵",
    "r": "車",
    "n": "馬",
    "b": "象",
    "a": "士",
    "k": "將",
    "c": "砲",
    "p": "卒",
}

PIECE_LIMITS = {
    "R": 2,
    "N": 2,
    "B": 2,
    "A": 2,
    "K": 1,
    "C": 2,
    "P": 5,
    "r": 2,
    "n": 2,
    "b": 2,
    "a": 2,
    "k": 1,
    "c": 2,
    "p": 5,
}


@dataclass(frozen=True)
class PositionIssue:
    code: str
    message: str
    squares: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    issues: tuple[PositionIssue, ...]


@dataclass(frozen=True)
class RecognitionResult:
    fen: str
    pieces: dict[str, str]
    active_color: str
    orientation: str
    confidence_by_square: dict[str, float]
    board_rectangle: BoardRectangle
    source_width: int
    source_height: int
    profile: str
    requires_confirmation: bool
    validation: ValidationResult


def recognize_image(
    source: bytes | str | Path | Image.Image,
    *,
    profile: str,
    active_color: str,
    board_rectangle: BoardRectangle | None = None,
) -> RecognitionResult:
    if profile != "scholars-studio":
        raise ValueError(f"Unsupported recognition profile: {profile!r}")
    if active_color not in {"w", "b"}:
        raise ValueError("active_color must be 'w' or 'b'")
    image = _load_image(source)
    rectangle = board_rectangle or _detect_scholars_studio_grid(image)
    cell_size = min(rectangle.width / 8, rectangle.height / 9)
    crop_size = max(20, int(round(cell_size * 0.82)))
    templates = _piece_templates(crop_size)
    pieces: dict[str, str] = {}
    confidence: dict[str, float] = {}
    for point in rectangle.grid_points():
        crop = _crop_centered(image, point.x, point.y, crop_size)
        piece, score = _classify_crop(crop, templates)
        if piece is not None:
            pieces[point.square] = piece
            confidence[point.square] = round(score, 4)

    validation = validate_piece_map(pieces, active_color=active_color)
    return RecognitionResult(
        fen=fen_from_piece_map(pieces, active_color=active_color),
        pieces=pieces,
        active_color=active_color,
        orientation=resolve_orientation(pieces),
        confidence_by_square=confidence,
        board_rectangle=rectangle,
        source_width=image.width,
        source_height=image.height,
        profile=profile,
        requires_confirmation=True,
        validation=validation,
    )


def validate_piece_map(pieces: Mapping[str, str], *, active_color: str) -> ValidationResult:
    issues: list[PositionIssue] = []
    if active_color not in {"w", "b"}:
        issues.append(PositionIssue("active_color", "Side to move must be Red or Black"))

    counts = Counter(pieces.values())
    for piece, count in sorted(counts.items()):
        limit = PIECE_LIMITS.get(piece)
        if limit is None:
            squares = tuple(sorted(square for square, value in pieces.items() if value == piece))
            issues.append(PositionIssue("unknown_piece", f"Unsupported piece {piece!r}", squares))
        elif count > limit:
            squares = tuple(sorted(square for square, value in pieces.items() if value == piece))
            issues.append(
                PositionIssue(
                    "piece_count",
                    f"Piece {piece} appears {count} times; at most {limit} are legal",
                    squares,
                )
            )

    _validate_general(pieces, "K", "red", {"d0", "e0", "f0", "d1", "e1", "f1", "d2", "e2", "f2"}, issues)
    _validate_general(pieces, "k", "black", {"d7", "e7", "f7", "d8", "e8", "f8", "d9", "e9", "f9"}, issues)

    red_general = _find_piece(pieces, "K")
    black_general = _find_piece(pieces, "k")
    if red_general and black_general and red_general[0] == black_general[0]:
        file_name = red_general[0]
        low, high = sorted((int(red_general[1]), int(black_general[1])))
        blockers = [
            f"{file_name}{rank}"
            for rank in range(low + 1, high)
            if f"{file_name}{rank}" in pieces
        ]
        if not blockers:
            issues.append(
                PositionIssue(
                    "facing_generals",
                    "The generals cannot face each other on an open file",
                    (red_general, black_general),
                )
            )
    return ValidationResult(valid=not issues, issues=tuple(issues))


def render_scholars_studio_board(
    fen: str,
    *,
    cell_size: int = 48,
    margin: int = 24,
) -> Image.Image:
    pieces = fen_to_piece_map(fen)
    surface_width = cell_size * 9
    surface_height = cell_size * 10
    image = Image.new("RGB", (surface_width + margin * 2 + 1, surface_height + margin * 2 + 1), PAPER)
    draw = ImageDraw.Draw(image)
    surface = (margin, margin, margin + surface_width, margin + surface_height)
    draw.rectangle(surface, fill=WOOD, outline=GRID, width=1)
    origin_x = margin + cell_size / 2
    origin_y = margin + cell_size / 2
    grid_width = cell_size * 8
    grid_height = cell_size * 9

    for row in range(10):
        y = origin_y + row * cell_size
        draw.line((origin_x, y, origin_x + grid_width, y), fill=GRID, width=1)
    for column in range(9):
        x = origin_x + column * cell_size
        if column in {0, 8}:
            draw.line((x, origin_y, x, origin_y + grid_height), fill=GRID, width=1)
        else:
            draw.line((x, origin_y, x, origin_y + cell_size * 4), fill=GRID, width=1)
            draw.line((x, origin_y + cell_size * 5, x, origin_y + grid_height), fill=GRID, width=1)
    draw.line((origin_x + cell_size * 3, origin_y, origin_x + cell_size * 5, origin_y + cell_size * 2), fill=GRID)
    draw.line((origin_x + cell_size * 5, origin_y, origin_x + cell_size * 3, origin_y + cell_size * 2), fill=GRID)
    draw.line((origin_x + cell_size * 3, origin_y + cell_size * 7, origin_x + cell_size * 5, origin_y + cell_size * 9), fill=GRID)
    draw.line((origin_x + cell_size * 5, origin_y + cell_size * 7, origin_x + cell_size * 3, origin_y + cell_size * 9), fill=GRID)

    font = _piece_font(max(12, int(round(cell_size * 0.45))))
    radius = cell_size * 0.38
    for square, piece in pieces.items():
        file_index = "abcdefghi".index(square[0])
        rank = int(square[1])
        center = (origin_x + file_index * cell_size, origin_y + (9 - rank) * cell_size)
        _draw_piece(draw, center, radius, piece, font)
    return image


def _detect_scholars_studio_grid(image: Image.Image) -> BoardRectangle:
    array = np.asarray(image.convert("RGB"), dtype=np.int16)
    distance = np.max(np.abs(array - np.asarray(WOOD, dtype=np.int16)), axis=2)
    ys, xs = np.where(distance <= 8)
    if len(xs) < 100:
        raise ValueError("Scholar's Studio board surface was not detected")
    left, right = max(0, int(xs.min()) - 1), min(image.width - 1, int(xs.max()) + 1)
    top, bottom = max(0, int(ys.min()) - 1), min(image.height - 1, int(ys.max()) + 1)
    surface_width = right - left
    surface_height = bottom - top
    cell_size = min(surface_width / 9, surface_height / 10)
    if cell_size < 16:
        raise ValueError("Detected board is too small to recognize")
    return BoardRectangle(
        x=left + cell_size / 2,
        y=top + cell_size / 2,
        width=cell_size * 8,
        height=cell_size * 9,
    )


def _piece_templates(size: int) -> dict[str, Image.Image]:
    font = _piece_font(max(12, int(round(size * 0.55))))
    radius = size * 0.46
    templates: dict[str, Image.Image] = {}
    for piece in PIECE_GLYPHS:
        image = Image.new("RGB", (size, size), WOOD)
        draw = ImageDraw.Draw(image)
        center = (size / 2, size / 2)
        draw.line((center[0], 0, center[0], size), fill=GRID, width=1)
        draw.line((0, center[1], size, center[1]), fill=GRID, width=1)
        _draw_piece(draw, center, radius, piece, font)
        templates[piece] = image
    return templates


def _classify_crop(crop: Image.Image, templates: Mapping[str, Image.Image]) -> tuple[str | None, float]:
    crop_array = np.asarray(crop.convert("RGB"), dtype=np.float32)
    best_piece: str | None = None
    best_score = -1.0
    for piece, template in templates.items():
        resized = template.resize(crop.size, Image.Resampling.LANCZOS)
        template_array = np.asarray(resized, dtype=np.float32)
        score = 1.0 - float(np.mean(np.abs(crop_array - template_array))) / 255.0
        if score > best_score:
            best_piece = piece
            best_score = score
    if best_score < 0.86:
        return None, best_score
    return best_piece, best_score


def _draw_piece(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
    radius: float,
    piece: str,
    font: ImageFont.ImageFont,
) -> None:
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=PIECE_FACE, outline=GRID, width=2)
    glyph = PIECE_GLYPHS[piece]
    fill = RED if piece.isupper() else BLACK
    bounds = draw.textbbox((0, 0), glyph, font=font)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    draw.text((x - text_width / 2, y - text_height / 2 - bounds[1]), glyph, font=font, fill=fill)


def _piece_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _crop_centered(image: Image.Image, x: float, y: float, size: int) -> Image.Image:
    half = size / 2
    return image.crop((round(x - half), round(y - half), round(x + half), round(y + half)))


def _load_image(source: bytes | str | Path | Image.Image) -> Image.Image:
    if isinstance(source, Image.Image):
        return source.convert("RGB")
    if isinstance(source, bytes):
        return Image.open(BytesIO(source)).convert("RGB")
    return Image.open(Path(source)).convert("RGB")


def _validate_general(
    pieces: Mapping[str, str],
    piece: str,
    color_name: str,
    palace: set[str],
    issues: list[PositionIssue],
) -> None:
    squares = tuple(sorted(square for square, value in pieces.items() if value == piece))
    if len(squares) != 1:
        issues.append(
            PositionIssue(
                f"{color_name}_general_count",
                f"Exactly one {color_name} general is required",
                squares,
            )
        )
    elif squares[0] not in palace:
        issues.append(
            PositionIssue(
                f"{color_name}_general_palace",
                f"The {color_name} general must be inside its palace",
                squares,
            )
        )


def _find_piece(pieces: Mapping[str, str], target: str) -> str | None:
    return next((square for square, piece in pieces.items() if piece == target), None)
