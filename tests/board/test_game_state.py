from xiangqi_sifu.board.game import GameState
from xiangqi_sifu.board.rules import BoardState, position_status
from xiangqi_sifu.vision.fen_from_image import fen_from_piece_map


def make_state(pieces: dict[str, str], active_color: str = "b") -> BoardState:
    return BoardState.from_fen(fen_from_piece_map(pieces, active_color=active_color))


def test_checkmate_and_stalemate_award_win_to_other_side():
    checkmate = make_state({"e9": "k", "e0": "K", "d8": "R", "e8": "R", "f8": "R"})
    stalemate = make_state({"e9": "k", "e0": "K", "e5": "P", "d8": "R", "f8": "R"})

    mate_status = position_status(checkmate)
    stale_status = position_status(stalemate)

    assert mate_status.kind == "checkmate"
    assert mate_status.winner == "red"
    assert stale_status.kind == "stalemate"
    assert stale_status.winner == "red"


def test_threefold_repetition_is_a_draw():
    board = make_state({"e9": "k", "e0": "K", "e5": "P"}, active_color="w")

    status = position_status(board, repetitions=3)

    assert status.kind == "draw_repetition"
    assert status.winner is None


def test_game_state_push_tracks_moves_and_repetitions_immutably():
    board = make_state({"e9": "k", "e0": "K", "e5": "P", "a0": "R"}, active_color="w")
    game = GameState.start(board)

    next_game = game.push("a0a1")

    assert game.moves == ()
    assert next_game.moves == ("a0a1",)
    assert next_game.board.piece_at("a1") == "R"
    assert next_game.repetition_count(next_game.board) == 1
