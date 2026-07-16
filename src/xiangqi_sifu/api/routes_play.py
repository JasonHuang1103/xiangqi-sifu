from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from xiangqi_sifu.api.dependencies import Services, get_services
from xiangqi_sifu.api.models import MoveRequest, NewGameRequest, ResignRequest
from xiangqi_sifu.api.serializers import stored_game_dict
from xiangqi_sifu.board.rules import BoardState, IllegalMoveError, apply_legal_move, legal_moves, position_status
from xiangqi_sifu.board.representation import Position

router = APIRouter(prefix="/api")


@router.post("/play/games")
def create_game(request: NewGameRequest, services: Services = Depends(get_services)) -> dict:
    if request.mode == "sifu" and request.human_side is None:
        raise HTTPException(status_code=422, detail="Sifu games require human_side")
    if request.mode == "sifu" and request.ai_level is None and not request.adaptive:
        raise HTTPException(status_code=422, detail="Choose an AI level or Adaptive")
    level = services.personal.adaptive_level() if request.adaptive else request.ai_level
    game = services.personal.create_game(
        mode=request.mode,
        human_side=request.human_side,
        ai_level=level,
        ai_adaptive=request.adaptive,
        red_name=request.red_name,
        black_name=request.black_name,
    )
    return stored_game_dict(game)


@router.get("/personal/games")
def list_personal_games(services: Services = Depends(get_services)) -> list[dict]:
    return [stored_game_dict(game) for game in services.personal.list_games()]


@router.get("/personal/games/{game_id}")
def get_personal_game(game_id: int, services: Services = Depends(get_services)) -> dict:
    try:
        return stored_game_dict(services.personal.get_game(game_id))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/play/games/{game_id}/moves")
def play_move(
    game_id: int,
    request: MoveRequest,
    services: Services = Depends(get_services),
) -> dict:
    try:
        game = services.personal.get_game(game_id)
        next_board = apply_legal_move(BoardState.from_fen(game.current_fen), request.uci)
        updated = services.personal.append_move(game_id, request.uci, next_board.to_fen())
        return _finish_if_terminal(updated, services)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (IllegalMoveError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/play/games/{game_id}/ai-move")
def play_ai_move(game_id: int, services: Services = Depends(get_services)) -> dict:
    if services.engine is None:
        raise HTTPException(status_code=503, detail="Pikafish is not configured")
    try:
        game = services.personal.get_game(game_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    if game.mode != "sifu":
        raise HTTPException(status_code=409, detail="This is not a Sifu game")
    board = BoardState.from_fen(game.current_fen)
    if board.active_color == game.human_side:
        raise HTTPException(status_code=409, detail="It is the human player's turn")
    position = Position(
        ply=len(game.moves),
        fen=board.to_fen(),
        side_to_move="red" if board.active_color == "w" else "black",
    )
    candidates = services.engine.analyze_lines(position, multipv=5)
    available = set(legal_moves(board))
    legal_candidates = [line.best_move for line in candidates if line.best_move in available]
    level = game.ai_level or 5
    pool_size = 1 if level == 10 else min(len(legal_candidates), max(2, 6 - level // 2))
    chosen = None if not legal_candidates else legal_candidates[(game.id + len(game.moves) + level) % pool_size]
    if chosen is None:
        raise HTTPException(status_code=503, detail="Pikafish returned no legal move")
    next_board = apply_legal_move(board, chosen)
    updated = services.personal.append_move(game_id, chosen, next_board.to_fen())
    return _finish_if_terminal(updated, services)


@router.post("/play/games/{game_id}/undo")
def undo_move(game_id: int, services: Services = Depends(get_services)) -> dict:
    try:
        game = services.personal.undo_last_move(game_id)
        if game.mode == "sifu" and game.moves and BoardState.from_fen(game.current_fen).active_color != game.human_side:
            game = services.personal.undo_last_move(game_id)
        return stored_game_dict(game)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/play/games/{game_id}/resign")
def resign_game(
    game_id: int,
    request: ResignRequest,
    services: Services = Depends(get_services),
) -> dict:
    try:
        game = services.personal.get_game(game_id)
        board = BoardState.from_fen(game.current_fen)
        side = request.side or (game.human_side if game.mode == "sifu" else board.active_color)
        result = "0-1" if side == "w" else "1-0"
        return stored_game_dict(services.personal.finish_game(game_id, result=result, termination="resignation"))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def _finish_if_terminal(game, services: Services) -> dict:
    board = BoardState.from_fen(game.current_fen)
    status = position_status(board)
    if status.terminal and game.status == "active":
        result = "1/2-1/2"
        if status.winner == "red":
            result = "1-0"
        elif status.winner == "black":
            result = "0-1"
        game = services.personal.finish_game(
            game.id, result=result, termination=status.kind
        )
    return stored_game_dict(game)
