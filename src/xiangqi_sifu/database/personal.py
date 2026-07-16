from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from xiangqi_sifu.config import DEFAULT_START_FEN


@dataclass(frozen=True)
class StoredMove:
    id: int
    ply: int
    uci: str
    resulting_fen: str


@dataclass(frozen=True)
class StoredGame:
    id: int
    mode: str
    status: str
    starting_fen: str
    current_fen: str
    human_side: str | None
    ai_level: int | None
    red_name: str | None
    black_name: str | None
    result: str | None
    termination: str | None
    created_at: str
    updated_at: str
    moves: tuple[StoredMove, ...]


class PersonalRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def create_game(
        self,
        *,
        mode: str,
        starting_fen: str = DEFAULT_START_FEN,
        human_side: str | None = None,
        ai_level: int | None = None,
        red_name: str | None = None,
        black_name: str | None = None,
    ) -> StoredGame:
        now = _timestamp()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO games (
                    mode, starting_fen, current_fen, human_side, ai_level,
                    red_name, black_name, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mode,
                    starting_fen,
                    starting_fen,
                    human_side,
                    ai_level,
                    red_name,
                    black_name,
                    now,
                    now,
                ),
            )
            game_id = int(cursor.lastrowid)
            connection.execute(
                "INSERT INTO game_events (game_id, event_type, created_at) VALUES (?, 'created', ?)",
                (game_id, now),
            )
        return self.get_game(game_id)

    def append_move(self, game_id: int, uci: str, resulting_fen: str) -> StoredGame:
        now = _timestamp()
        with self._connect() as connection:
            game = connection.execute(
                "SELECT status FROM games WHERE id = ?", (game_id,)
            ).fetchone()
            if game is None:
                raise KeyError(f"Personal game not found: {game_id}")
            if game["status"] != "active":
                raise ValueError("Cannot append a move to a completed game")
            ply = int(
                connection.execute(
                    "SELECT COUNT(*) FROM moves WHERE game_id = ? AND retracted = 0",
                    (game_id,),
                ).fetchone()[0]
            ) + 1
            connection.execute(
                """
                INSERT INTO moves (game_id, ply, uci, resulting_fen, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (game_id, ply, uci.lower(), resulting_fen, now),
            )
            connection.execute(
                "UPDATE games SET current_fen = ?, updated_at = ? WHERE id = ?",
                (resulting_fen, now, game_id),
            )
            connection.execute(
                """
                INSERT INTO game_events (game_id, event_type, payload_json, created_at)
                VALUES (?, 'move', ?, ?)
                """,
                (game_id, json.dumps({"ply": ply, "uci": uci.lower()}), now),
            )
        return self.get_game(game_id)

    def undo_last_move(self, game_id: int) -> StoredGame:
        now = _timestamp()
        with self._connect() as connection:
            game = connection.execute(
                "SELECT starting_fen, status FROM games WHERE id = ?", (game_id,)
            ).fetchone()
            if game is None:
                raise KeyError(f"Personal game not found: {game_id}")
            if game["status"] != "active":
                raise ValueError("Cannot undo a completed game")
            latest = connection.execute(
                """
                SELECT id, ply, uci FROM moves
                WHERE game_id = ? AND retracted = 0
                ORDER BY ply DESC, id DESC LIMIT 1
                """,
                (game_id,),
            ).fetchone()
            if latest is None:
                raise ValueError("No move is available to undo")
            connection.execute("UPDATE moves SET retracted = 1 WHERE id = ?", (latest["id"],))
            previous = connection.execute(
                """
                SELECT resulting_fen FROM moves
                WHERE game_id = ? AND retracted = 0
                ORDER BY ply DESC, id DESC LIMIT 1
                """,
                (game_id,),
            ).fetchone()
            current_fen = previous["resulting_fen"] if previous else game["starting_fen"]
            connection.execute(
                "UPDATE games SET current_fen = ?, updated_at = ? WHERE id = ?",
                (current_fen, now, game_id),
            )
            connection.execute(
                """
                INSERT INTO game_events (game_id, event_type, payload_json, created_at)
                VALUES (?, 'undo', ?, ?)
                """,
                (
                    game_id,
                    json.dumps({"ply": latest["ply"], "uci": latest["uci"]}),
                    now,
                ),
            )
        return self.get_game(game_id)

    def finish_game(self, game_id: int, *, result: str, termination: str) -> StoredGame:
        now = _timestamp()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE games
                SET status = 'completed', result = ?, termination = ?, updated_at = ?
                WHERE id = ?
                """,
                (result, termination, now, game_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"Personal game not found: {game_id}")
            connection.execute(
                """
                INSERT INTO game_events (game_id, event_type, payload_json, created_at)
                VALUES (?, 'finished', ?, ?)
                """,
                (game_id, json.dumps({"result": result, "termination": termination}), now),
            )
        return self.get_game(game_id)

    def get_game(self, game_id: int) -> StoredGame:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
            if row is None:
                raise KeyError(f"Personal game not found: {game_id}")
            return self._stored_game(connection, row)

    def list_games(self) -> list[StoredGame]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM games
                ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, updated_at DESC, id DESC
                """
            ).fetchall()
            return [self._stored_game(connection, row) for row in rows]

    def _stored_game(self, connection: sqlite3.Connection, row: sqlite3.Row) -> StoredGame:
        move_rows = connection.execute(
            """
            SELECT id, ply, uci, resulting_fen FROM moves
            WHERE game_id = ? AND retracted = 0
            ORDER BY ply, id
            """,
            (row["id"],),
        ).fetchall()
        return StoredGame(
            id=row["id"],
            mode=row["mode"],
            status=row["status"],
            starting_fen=row["starting_fen"],
            current_fen=row["current_fen"],
            human_side=row["human_side"],
            ai_level=row["ai_level"],
            red_name=row["red_name"],
            black_name=row["black_name"],
            result=row["result"],
            termination=row["termination"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            moves=tuple(
                StoredMove(
                    id=move["id"],
                    ply=move["ply"],
                    uci=move["uci"],
                    resulting_fen=move["resulting_fen"],
                )
                for move in move_rows
            ),
        )

    def _migrate(self) -> None:
        schema = Path(__file__).with_name("personal_schema.sql").read_text(encoding="utf-8")
        with self._connect() as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version > 1:
                raise RuntimeError(f"personal.db schema version {version} is newer than supported")
            if version == 0:
                connection.executescript(schema)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")
