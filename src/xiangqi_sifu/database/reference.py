from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReferenceGameSummary:
    id: int
    corpus_name: str
    source_game_id: int
    event: str | None
    red: str | None
    black: str | None
    result: str | None
    move_count: int


@dataclass(frozen=True)
class ReferenceGamePage:
    total: int
    offset: int
    limit: int
    games: tuple[ReferenceGameSummary, ...]


@dataclass(frozen=True)
class ReferenceGameDetail:
    summary: ReferenceGameSummary
    record: dict[str, Any]


class ReferenceRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"Reference database not found: {self.path}")

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(f"{self.path.resolve().as_uri()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection

    def search_games(
        self,
        query: str = "",
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> ReferenceGamePage:
        if offset < 0:
            raise ValueError("offset cannot be negative")
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        pattern = f"%{query.strip().lower()}%"
        where = """
            lower(coalesce(event, '') || ' ' || coalesce(red, '') || ' ' ||
                  coalesce(black, '') || ' ' || coalesce(result, '')) like ?
        """
        with self.connect() as connection:
            total = int(
                connection.execute(f"SELECT COUNT(*) FROM kb_games WHERE {where}", (pattern,)).fetchone()[0]
            )
            rows = connection.execute(
                f"""
                SELECT id, corpus_name, source_game_id, event, red, black, result, move_count
                FROM kb_games
                WHERE {where}
                ORDER BY id
                LIMIT ? OFFSET ?
                """,
                (pattern, limit, offset),
            ).fetchall()
        return ReferenceGamePage(
            total=total,
            offset=offset,
            limit=limit,
            games=tuple(_summary(row) for row in rows),
        )

    def get_game(self, game_id: int) -> ReferenceGameDetail:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, corpus_name, source_file, source_game_id, event, red, black,
                       result, move_count
                FROM kb_games WHERE id = ?
                """,
                (game_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Reference game not found: {game_id}")
        record = _read_jsonl_record(Path(row["source_file"]), int(row["source_game_id"]))
        return ReferenceGameDetail(summary=_summary(row), record=record)


def _summary(row: sqlite3.Row) -> ReferenceGameSummary:
    return ReferenceGameSummary(
        id=int(row["id"]),
        corpus_name=str(row["corpus_name"]),
        source_game_id=int(row["source_game_id"]),
        event=row["event"],
        red=row["red"],
        black=row["black"],
        result=row["result"],
        move_count=int(row["move_count"]),
    )


def _read_jsonl_record(path: Path, source_game_id: int) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Reference game source not found: {path}")
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if line_number == source_game_id:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError(f"Reference game {source_game_id} is not an object")
                return record
    raise KeyError(f"Reference source game not found: {source_game_id}")
