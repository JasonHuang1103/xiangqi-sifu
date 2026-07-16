from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    engine_available: bool
    personal_db: str
    reference_db: str
