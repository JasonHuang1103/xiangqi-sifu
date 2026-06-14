"""Screenshot-to-FEN vision helpers for Phase 3.5."""

from xiangqi_sifu.vision.fen_from_image import fen_from_piece_map, fen_to_piece_map
from xiangqi_sifu.vision.grid_mapper import BoardRectangle, GridPoint
from xiangqi_sifu.vision.image_recognizer import TemplatePieceRecognizer, recognize_board_from_image
from xiangqi_sifu.vision.move_from_screenshots import MoveInference, infer_move_from_fens
from xiangqi_sifu.vision.orientation import resolve_orientation

__all__ = [
    "BoardRectangle",
    "GridPoint",
    "MoveInference",
    "TemplatePieceRecognizer",
    "fen_from_piece_map",
    "fen_to_piece_map",
    "infer_move_from_fens",
    "recognize_board_from_image",
    "resolve_orientation",
]
