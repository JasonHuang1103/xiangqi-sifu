from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request

from xiangqi_sifu.coach.chat import CoachService
from xiangqi_sifu.database.personal import PersonalRepository
from xiangqi_sifu.database.reference import ReferenceRepository


@dataclass(frozen=True)
class Services:
    personal: PersonalRepository
    reference: ReferenceRepository | None
    engine: Any | None
    coach: CoachService


def get_services(request: Request) -> Services:
    return request.app.state.services
