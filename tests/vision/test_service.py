from io import BytesIO

from xiangqi_sifu.config import DEFAULT_START_FEN
from xiangqi_sifu.vision.fen_from_image import fen_to_piece_map
from xiangqi_sifu.vision.service import (
    recognize_image,
    render_scholars_studio_board,
    validate_piece_map,
)


def test_scholars_studio_screenshot_round_trips_starting_position():
    image = render_scholars_studio_board(DEFAULT_START_FEN, cell_size=48, margin=24)
    raw = BytesIO()
    image.save(raw, format="PNG")

    result = recognize_image(raw.getvalue(), profile="scholars-studio", active_color="w")

    assert result.fen == DEFAULT_START_FEN
    assert len(result.pieces) == 32
    assert result.orientation == "red_bottom"
    assert result.requires_confirmation is True
    assert result.board_rectangle.width == 48 * 8
    assert result.board_rectangle.height == 48 * 9
    assert set(result.confidence_by_square) == set(result.pieces)


def test_position_validation_reports_missing_and_misplaced_generals():
    pieces = fen_to_piece_map(DEFAULT_START_FEN)
    pieces.pop("e0")
    pieces["a0"] = "K"

    result = validate_piece_map(pieces, active_color="w")

    assert result.valid is False
    assert any(issue.code == "red_general_palace" and issue.squares == ("a0",) for issue in result.issues)


def test_position_validation_reports_excess_pieces_and_facing_generals():
    pieces = {"e0": "K", "e9": "k", "a0": "R", "b0": "R", "c0": "R"}

    result = validate_piece_map(pieces, active_color="b")

    assert any(issue.code == "piece_count" and "R" in issue.message for issue in result.issues)
    assert any(issue.code == "facing_generals" for issue in result.issues)


def test_valid_start_position_has_no_validation_issues():
    result = validate_piece_map(fen_to_piece_map(DEFAULT_START_FEN), active_color="w")

    assert result.valid is True
    assert result.issues == ()
