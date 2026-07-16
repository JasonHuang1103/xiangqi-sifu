from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    engine_available: bool
    personal_db: str
    reference_db: str


class FenRequest(BaseModel):
    fen: str


class PositionAnalysisRequest(BaseModel):
    fen: str
    multipv: int = Field(default=3, ge=1, le=10)


class GameAnalysisRequest(BaseModel):
    starting_fen: str
    moves: list[str]
    multipv: int = Field(default=1, ge=1, le=5)


class RecordInspectRequest(BaseModel):
    text: str
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


class NewGameRequest(BaseModel):
    mode: Literal["friend", "sifu"]
    human_side: Literal["w", "b"] | None = None
    ai_level: int | None = Field(default=None, ge=1, le=10)
    red_name: str | None = None
    black_name: str | None = None


class MoveRequest(BaseModel):
    uci: str


class CoachThreadRequest(BaseModel):
    fen: str
    side_to_move: Literal["red", "black"]
    best_move: str | None = None
    red_score_cp: int | None = None
    mate_score: int | None = None
    pv: list[str] = Field(default_factory=list)
    selected_ply: int | None = None
    played_move: str | None = None
    mover_loss_cp: int | None = None
    game_id: int | None = None


class CoachMessageRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
