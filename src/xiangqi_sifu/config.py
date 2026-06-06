from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_START_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


@dataclass(frozen=True)
class AppConfig:
    engine_path: Path | None
    database_path: Path


def load_config() -> AppConfig:
    engine_value = os.environ.get("XIANGQI_SIFU_ENGINE_PATH")
    db_value = os.environ.get("XIANGQI_SIFU_DB_PATH", "xiangqi_sifu.db")
    return AppConfig(
        engine_path=Path(engine_value).expanduser() if engine_value else None,
        database_path=Path(db_value).expanduser(),
    )
