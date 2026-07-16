from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from xiangqi_sifu.api.dependencies import Services, get_services

router = APIRouter(prefix="/api")


@router.get("/reference/games")
def search_reference_games(
    query: str = "",
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    services: Services = Depends(get_services),
) -> dict:
    if services.reference is None:
        raise HTTPException(status_code=503, detail="Tournament library is not configured")
    page = services.reference.search_games(query, offset=offset, limit=limit)
    return {
        "total": page.total,
        "offset": page.offset,
        "limit": page.limit,
        "games": [game.__dict__ for game in page.games],
    }


@router.get("/reference/games/{game_id}")
def get_reference_game(game_id: int, services: Services = Depends(get_services)) -> dict:
    if services.reference is None:
        raise HTTPException(status_code=503, detail="Tournament library is not configured")
    try:
        detail = services.reference.get_game(game_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {"summary": detail.summary.__dict__, "record": detail.record}
