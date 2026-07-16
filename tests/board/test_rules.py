import pytest

from xiangqi_sifu.board.rules import (
    BoardState,
    IllegalMoveError,
    apply_legal_move,
    is_in_check,
    legal_moves,
)
from xiangqi_sifu.vision.fen_from_image import fen_from_piece_map


def state(pieces: dict[str, str], active_color: str = "w") -> BoardState:
    return BoardState.from_fen(fen_from_piece_map(pieces, active_color=active_color))


def with_kings(**pieces: str) -> dict[str, str]:
    return {"e0": "K", "e9": "k", "e5": "P", **pieces}


def test_general_and_advisor_stay_inside_the_palace():
    board = state(with_kings(e1="A"))

    moves = set(legal_moves(board))

    assert {"e0d0", "e0f0", "e1d2", "e1f2"} <= moves
    assert "e1e2" not in moves
    assert "e0c0" not in moves


def test_elephant_cannot_cross_river_or_jump_a_blocked_eye():
    open_board = state(with_kings(c2="B"))
    blocked_board = state(with_kings(c2="B", b3="P"))

    assert "c2a4" in legal_moves(open_board)
    assert "c2e4" in legal_moves(open_board)
    assert "c2e6" not in legal_moves(open_board)
    assert "c2a4" not in legal_moves(blocked_board)


def test_horse_leg_blocks_both_destinations_on_that_side():
    open_board = state(with_kings(b0="N"))
    blocked_board = state(with_kings(b0="N", b1="P"))

    assert {"b0a2", "b0c2", "b0d1"} <= set(legal_moves(open_board))
    assert "b0a2" not in legal_moves(blocked_board)
    assert "b0c2" not in legal_moves(blocked_board)
    assert "b0d1" in legal_moves(blocked_board)


def test_rook_stops_at_blocker_and_cannon_needs_exactly_one_screen_to_capture():
    rook_board = state(with_kings(a0="R", a2="P"))
    cannon_board = state(with_kings(a0="C", a1="P", a3="r"))

    assert "a0a1" in legal_moves(rook_board)
    assert "a0a3" not in legal_moves(rook_board)
    assert "a0a3" in legal_moves(cannon_board)
    assert "a0a2" not in legal_moves(cannon_board)


def test_soldier_gains_sideways_moves_only_after_crossing_the_river():
    red_before = state(with_kings(d4="P"))
    red_after = state({"e0": "K", "e9": "k", "e4": "P", "d5": "P"})
    black_after = state({"e0": "K", "e9": "k", "e6": "p", "d4": "p"}, active_color="b")

    assert "d4d5" in legal_moves(red_before)
    assert "d4c4" not in legal_moves(red_before)
    assert {"d5d6", "d5c5", "d5e5"} <= set(legal_moves(red_after))
    assert {"d4d3", "d4c4", "d4e4"} <= set(legal_moves(black_after))


def test_flying_generals_attack_each_other_on_an_open_file():
    board = state({"e0": "K", "e9": "k"})

    assert is_in_check(board, "w")
    assert is_in_check(board, "b")
    assert "e0e9" in legal_moves(board)


def test_move_that_exposes_own_general_is_illegal():
    board = state({"e0": "K", "e9": "r", "e1": "R", "d9": "k"})

    assert "e1d1" not in legal_moves(board)
    with pytest.raises(IllegalMoveError):
        apply_legal_move(board, "e1d1")


def test_apply_legal_move_switches_side_and_preserves_fen_fields():
    board = BoardState.from_fen(
        "4k4/9/9/9/4p4/4P4/9/4C4/9/4K4 w - - 7 12"
    )

    moved = apply_legal_move(board, "e2d2")

    assert moved.piece_at("d2") == "C"
    assert moved.active_color == "b"
    assert moved.fullmove_number == 12
    assert moved.halfmove_clock == 8
