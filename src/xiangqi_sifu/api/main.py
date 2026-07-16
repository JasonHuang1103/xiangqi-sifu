from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from xiangqi_sifu.api.dependencies import Services
from xiangqi_sifu.api.models import HealthResponse
from xiangqi_sifu.api.routes_analysis import router as analysis_router
from xiangqi_sifu.api.routes_coach import router as coach_router
from xiangqi_sifu.api.routes_library import router as library_router
from xiangqi_sifu.api.routes_play import router as play_router
from xiangqi_sifu.api.routes_records import router as records_router
from xiangqi_sifu.coach.chat import CoachService
from xiangqi_sifu.database.personal import PersonalRepository
from xiangqi_sifu.database.reference import ReferenceRepository
from xiangqi_sifu.engine.pikafish import PikafishEngine


def create_app(
    *,
    data_dir: str | Path = "data/processed",
    engine_path: str | Path | None = None,
    reference_path: str | Path | None = None,
    engine: Any | None = None,
) -> FastAPI:
    storage = Path(data_dir)
    configured_engine_path = Path(engine_path) if engine_path is not None else None
    configured_engine = engine
    if configured_engine is None and configured_engine_path is not None and configured_engine_path.is_file():
        configured_engine = PikafishEngine(configured_engine_path)
    personal_db = storage / "personal.db"
    reference_db = Path(reference_path) if reference_path is not None else storage / "reference.db"
    fallback_reference = storage / "xiangqi_sifu_knowledge.db"
    actual_reference = reference_db if reference_db.is_file() else fallback_reference
    reference = ReferenceRepository(actual_reference) if actual_reference.is_file() else None
    services = Services(
        personal=PersonalRepository(personal_db),
        reference=reference,
        engine=configured_engine,
        coach=CoachService(),
    )

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        yield
        close = getattr(configured_engine, "close", None)
        if close is not None:
            close()

    application = FastAPI(title="Xiangqi Sifu", version="0.2.0", lifespan=lifespan)
    application.state.services = services

    @application.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            engine_available=configured_engine is not None,
            personal_db=str(personal_db),
            reference_db=str(reference_db),
        )

    application.include_router(analysis_router)
    application.include_router(records_router)
    application.include_router(play_router)
    application.include_router(coach_router)
    application.include_router(library_router)
    return application


app = create_app()
