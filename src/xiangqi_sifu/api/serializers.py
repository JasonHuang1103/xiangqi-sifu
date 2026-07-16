from __future__ import annotations

from dataclasses import asdict

from xiangqi_sifu.analysis.service import estimated_red_win_rate
from xiangqi_sifu.board.rules import BoardState, legal_moves, position_status
from xiangqi_sifu.database.personal import StoredCoachThread, StoredGame
from xiangqi_sifu.vision.fen_from_image import fen_to_piece_map


def engine_line_dict(line) -> dict:
    data = asdict(line)
    data["pv"] = list(line.pv)
    data["estimated_red_win_rate"] = (
        None if line.mate_score is not None else estimated_red_win_rate(line.red_score_cp)
    )
    return data


def stored_game_dict(game: StoredGame) -> dict:
    board = BoardState.from_fen(game.current_fen)
    repetitions = 1
    status = position_status(board, repetitions=repetitions)
    return {
        "id": game.id,
        "mode": game.mode,
        "status": game.status,
        "starting_fen": game.starting_fen,
        "current_fen": game.current_fen,
        "human_side": game.human_side,
        "ai_level": game.ai_level,
        "ai_adaptive": game.ai_adaptive,
        "red_name": game.red_name,
        "black_name": game.black_name,
        "result": game.result,
        "termination": game.termination,
        "created_at": game.created_at,
        "updated_at": game.updated_at,
        "side_to_move": "red" if board.active_color == "w" else "black",
        "pieces": fen_to_piece_map(game.current_fen),
        "legal_moves": list(legal_moves(board)) if game.status == "active" else [],
        "position_status": asdict(status),
        "moves": [asdict(move) for move in game.moves],
    }


def coach_thread_dict(thread: StoredCoachThread) -> dict:
    return {
        "id": thread.id,
        "game_id": thread.game_id,
        "context": thread.context,
        "selected_ply": thread.selected_ply,
        "messages": [asdict(message) for message in thread.messages],
    }
