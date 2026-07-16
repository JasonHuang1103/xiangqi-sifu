from __future__ import annotations

import re
from dataclasses import dataclass

from xiangqi_sifu.parsers.base import GameRecord
from xiangqi_sifu.parsers.pgn_parser import PgnParser, TAG_RE
from xiangqi_sifu.parsers.simple_move_parser import MOVE_TOKEN_RE, SimpleMoveParser
from xiangqi_sifu.parsers.wxf_bulk_parser import GAME_DELIMITER

GAME_START_RE = re.compile(r'(?=^\[Game "Chinese Chess"\]\s*$)', re.MULTILINE)
SUSPICIOUS_BODY_TOKEN_RE = re.compile(r"\b[A-Za-z]+(?:-[A-Za-z]+)+\b")


class RecordInspectionError(ValueError):
    def __init__(self, game_index: int, detail: str) -> None:
        self.game_index = game_index
        self.detail = detail
        super().__init__(f"Game {game_index + 1}: {detail}")


@dataclass(frozen=True)
class RecordGameSummary:
    index: int
    event: str | None
    red: str | None
    black: str | None
    result: str | None
    move_count: int
    starting_fen: str
    record: GameRecord


@dataclass(frozen=True)
class RecordInspection:
    total_games: int
    offset: int
    limit: int
    games: tuple[RecordGameSummary, ...]

    @property
    def requires_selection(self) -> bool:
        return self.total_games > 1


def inspect_record(text: str, *, offset: int = 0, limit: int = 50) -> RecordInspection:
    if offset < 0:
        raise ValueError("offset cannot be negative")
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200")
    raw_games = _split_games(text)
    if not raw_games:
        raise RecordInspectionError(0, "No game record was found")

    parsed: list[RecordGameSummary] = []
    for index, raw_game in enumerate(raw_games):
        _reject_unsupported_tokens(raw_game, game_index=index)
        try:
            record = (
                PgnParser().parse_text(raw_game)
                if "[" in raw_game
                else SimpleMoveParser().parse_text(raw_game)
            )
        except ValueError as error:
            raise RecordInspectionError(index, str(error)) from error
        if not record.moves:
            raise RecordInspectionError(index, "No supported ICCS moves were found")
        parsed.append(
            RecordGameSummary(
                index=index,
                event=record.metadata.get("Event"),
                red=record.red,
                black=record.black,
                result=record.result,
                move_count=len(record.moves),
                starting_fen=record.starting_fen,
                record=record,
            )
        )
    return RecordInspection(
        total_games=len(parsed),
        offset=offset,
        limit=limit,
        games=tuple(parsed[offset : offset + limit]),
    )


def _split_games(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    if GAME_DELIMITER not in cleaned:
        return [cleaned]
    return [part.strip() for part in GAME_START_RE.split(cleaned) if part.strip()]


def _reject_unsupported_tokens(raw_game: str, *, game_index: int) -> None:
    body = TAG_RE.sub("", raw_game)
    for token in SUSPICIOUS_BODY_TOKEN_RE.findall(body):
        if MOVE_TOKEN_RE.fullmatch(token) is None:
            raise RecordInspectionError(game_index, f"Unsupported move token: {token}")
