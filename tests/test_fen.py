from xiangqi_sifu.board.fen import FenBoard, generate_positions


START_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


def test_fen_board_applies_coordinate_move_without_legal_validation():
    board = FenBoard.from_fen(START_FEN)

    next_board = board.apply_uci_move("h2e2")

    assert next_board.piece_at("h2") is None
    assert next_board.piece_at("e2") == "C"
    assert next_board.active_color == "b"
    assert next_board.to_fen().startswith("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR b")


def test_generate_positions_includes_start_and_after_each_move():
    positions = generate_positions(START_FEN, ["h2e2", "b9c7"])

    assert len(positions) == 3
    assert positions[0].ply == 0
    assert positions[1].move_uci == "h2e2"
    assert positions[1].side_to_move == "black"
    assert positions[2].move_uci == "b9c7"
    assert positions[2].side_to_move == "red"
