from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from xiangqi_sifu.api.dependencies import Services, get_services
from xiangqi_sifu.api.models import FenRequest, GameAnalysisRequest, PositionAnalysisRequest
from xiangqi_sifu.api.serializers import engine_line_dict
from xiangqi_sifu.board.rules import BoardState
from xiangqi_sifu.board.rules import IllegalMoveError, apply_legal_move
from xiangqi_sifu.board.representation import Position
from xiangqi_sifu.vision.fen_from_image import fen_to_piece_map
from xiangqi_sifu.vision.service import recognize_image, validate_piece_map

router = APIRouter(prefix="/api")


@router.post("/positions/validate")
def validate_position(request: FenRequest) -> dict:
    try:
        board = BoardState.from_fen(request.fen)
        pieces = fen_to_piece_map(board.to_fen())
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    validation = validate_piece_map(pieces, active_color=board.active_color)
    return {
        "fen": board.to_fen(),
        "pieces": pieces,
        "active_color": board.active_color,
        "valid": validation.valid,
        "issues": [asdict(issue) for issue in validation.issues],
    }


@router.post("/positions/recognize")
async def recognize_position(
    image: UploadFile = File(),
    profile: str = Form(default="scholars-studio"),
    active_color: str = Form(default="w"),
) -> dict:
    try:
        result = recognize_image(
            await image.read(), profile=profile, active_color=active_color
        )
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        **asdict(result),
        "board_rectangle": asdict(result.board_rectangle),
        "validation": {
            "valid": result.validation.valid,
            "issues": [asdict(issue) for issue in result.validation.issues],
        },
    }


@router.post("/analysis/positions")
def analyze_position(
    request: PositionAnalysisRequest,
    services: Services = Depends(get_services),
) -> dict:
    if services.engine is None:
        raise HTTPException(status_code=503, detail="Pikafish is not configured")
    try:
        board = BoardState.from_fen(request.fen)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    position = Position(
        ply=0,
        fen=board.to_fen(),
        side_to_move="red" if board.active_color == "w" else "black",
    )
    lines = services.engine.analyze_lines(position, multipv=request.multipv)
    return {"fen": board.to_fen(), "lines": [engine_line_dict(line) for line in lines]}


@router.post("/analysis/games")
def analyze_game_positions(
    request: GameAnalysisRequest,
    services: Services = Depends(get_services),
) -> dict:
    if services.engine is None:
        raise HTTPException(status_code=503, detail="Pikafish is not configured")
    try:
        board = BoardState.from_fen(request.starting_fen)
        positions: list[tuple[BoardState, str | None]] = [(board, None)]
        for move in request.moves:
            board = apply_legal_move(board, move)
            positions.append((board, move.lower()))
    except (IllegalMoveError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    rows = []
    for ply, (position_board, played_move) in enumerate(positions):
        position = Position(
            ply=ply,
            fen=position_board.to_fen(),
            side_to_move="red" if position_board.active_color == "w" else "black",
        )
        lines = services.engine.analyze_lines(position, multipv=request.multipv)
        rows.append(
            {
                "ply": ply,
                "fen": position_board.to_fen(),
                "played_move": played_move,
                "lines": [engine_line_dict(line) for line in lines],
            }
        )
    return {"starting_fen": request.starting_fen, "moves": request.moves, "positions": rows}
