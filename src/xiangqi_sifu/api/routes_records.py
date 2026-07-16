from __future__ import annotations

from fastapi import APIRouter, HTTPException

from xiangqi_sifu.api.models import RecordInspectRequest
from xiangqi_sifu.records.service import RecordInspectionError, inspect_record

router = APIRouter(prefix="/api")


@router.post("/records/inspect")
def inspect_uploaded_record(request: RecordInspectRequest) -> dict:
    try:
        inspection = inspect_record(request.text, offset=request.offset, limit=request.limit)
    except RecordInspectionError as error:
        raise HTTPException(
            status_code=422,
            detail={"game_index": error.game_index, "message": error.detail},
        ) from error
    return {
        "total_games": inspection.total_games,
        "offset": inspection.offset,
        "limit": inspection.limit,
        "requires_selection": inspection.requires_selection,
        "games": [
            {
                "index": game.index,
                "event": game.event,
                "red": game.red,
                "black": game.black,
                "result": game.result,
                "move_count": game.move_count,
                "starting_fen": game.starting_fen,
                "moves": [move.uci for move in game.record.moves],
            }
            for game in inspection.games
        ],
    }
