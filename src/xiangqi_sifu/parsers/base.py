from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from xiangqi_sifu.config import DEFAULT_START_FEN


@dataclass(frozen=True)
class ParsedMove:
    iccs: str
    uci: str
    move_number: int
    side: str


@dataclass(frozen=True)
class GameRecord:
    metadata: dict[str, str] = field(default_factory=dict)
    starting_fen: str = DEFAULT_START_FEN
    moves: list[ParsedMove] = field(default_factory=list)
    red: str | None = None
    black: str | None = None
    result: str | None = None


class GameParser(Protocol):
    def parse_text(self, text: str) -> GameRecord:
        ...

    def parse_file(self, path: str | Path) -> GameRecord:
        ...
