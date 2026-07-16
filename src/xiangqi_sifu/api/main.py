from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from xiangqi_sifu.api.models import HealthResponse


def create_app(
    *,
    data_dir: str | Path = "data/processed",
    engine_path: str | Path | None = None,
) -> FastAPI:
    storage = Path(data_dir)
    engine = Path(engine_path) if engine_path is not None else None
    personal_db = storage / "personal.db"
    reference_db = storage / "reference.db"

    application = FastAPI(title="Xiangqi Sifu", version="0.2.0")

    @application.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            engine_available=engine is not None and engine.is_file(),
            personal_db=str(personal_db),
            reference_db=str(reference_db),
        )

    return application


app = create_app()
