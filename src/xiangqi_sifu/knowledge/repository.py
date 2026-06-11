from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class KnowledgeBaseRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save_game(self, record: dict[str, Any], *, corpus_name: str, source_file: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("pragma foreign_keys = on")
            return self.save_game_in_connection(
                conn,
                record,
                corpus_name=corpus_name,
                source_file=source_file,
            )

    def save_game_in_connection(
        self,
        conn: sqlite3.Connection,
        record: dict[str, Any],
        *,
        corpus_name: str,
        source_file: str,
    ) -> int:
        metadata = record.get("metadata") or {}
        cursor = conn.execute(
            """
            insert or ignore into kb_games (
                corpus_name, source_file, source_game_id, event, red, black, result,
                starting_fen, move_count, metadata_json
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corpus_name,
                source_file,
                int(record["game_id"]),
                metadata.get("Event"),
                record.get("red"),
                record.get("black"),
                record.get("result"),
                record["starting_fen"],
                int(record.get("move_count", len(record.get("moves", [])))),
                json.dumps(metadata, ensure_ascii=False),
            ),
        )
        if cursor.lastrowid:
            return int(cursor.lastrowid)
        row = conn.execute(
            """
            select id from kb_games
            where corpus_name = ? and source_file = ? and source_game_id = ?
            """,
            (corpus_name, source_file, int(record["game_id"])),
        ).fetchone()
        return int(row[0])

    def add_position_move(
        self,
        *,
        fen: str,
        side_to_move: str,
        move_uci: str,
        move_iccs: str,
        side: str,
        result: str | None,
        game_id: int,
        ply: int,
        max_examples_per_move: int,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("pragma foreign_keys = on")
            self.add_position_move_in_connection(
                conn,
                fen=fen,
                side_to_move=side_to_move,
                move_uci=move_uci,
                move_iccs=move_iccs,
                side=side,
                result=result,
                game_id=game_id,
                ply=ply,
                max_examples_per_move=max_examples_per_move,
            )

    def add_position_move_in_connection(
        self,
        conn: sqlite3.Connection,
        *,
        fen: str,
        side_to_move: str,
        move_uci: str,
        move_iccs: str,
        side: str,
        result: str | None,
        game_id: int,
        ply: int,
        max_examples_per_move: int,
    ) -> None:
        red_win, black_win, draw = _result_counts(result)
        conn.execute(
            """
            insert into kb_positions (fen, side_to_move, occurrence_count)
            values (?, ?, 1)
            on conflict(fen) do update set
                occurrence_count = occurrence_count + 1
            """,
            (fen, side_to_move),
        )
        conn.execute(
            """
            insert into kb_moves (
                fen, move_uci, move_iccs, side, play_count,
                red_wins, black_wins, draws, sample_game_id, sample_ply
            )
            values (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
            on conflict(fen, move_uci) do update set
                play_count = play_count + 1,
                red_wins = red_wins + excluded.red_wins,
                black_wins = black_wins + excluded.black_wins,
                draws = draws + excluded.draws
            """,
            (
                fen,
                move_uci,
                move_iccs,
                side,
                red_win,
                black_win,
                draw,
                game_id,
                ply,
            ),
        )
        example_count = conn.execute(
            """
            select count(*) from kb_examples
            where fen = ? and move_uci = ?
            """,
            (fen, move_uci),
        ).fetchone()[0]
        if example_count < max_examples_per_move:
            conn.execute(
                """
                insert or ignore into kb_examples (fen, move_uci, game_id, ply)
                values (?, ?, ?, ?)
                """,
                (fen, move_uci, game_id, ply),
            )

    def get_position_summary(self, fen: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "select fen, side_to_move, occurrence_count from kb_positions where fen = ?",
                (fen,),
            ).fetchone()
        return dict(row) if row is not None else None

    def get_position_moves(self, fen: str, *, limit: int = 10) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                select move_uci, move_iccs, side, play_count, red_wins, black_wins, draws,
                       sample_game_id, sample_ply
                from kb_moves
                where fen = ?
                order by play_count desc, move_uci asc
                limit ?
                """,
                (fen, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_representative_games(
        self,
        fen: str,
        move_uci: str | None = None,
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [fen]
        move_filter = ""
        if move_uci is not None:
            move_filter = "and e.move_uci = ?"
            params.append(move_uci)
        params.append(limit)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""
                select e.ply, e.move_uci, g.corpus_name, g.source_file, g.source_game_id,
                       g.event, g.red, g.black, g.result
                from kb_examples e
                join kb_games g on g.id = e.game_id
                where e.fen = ?
                {move_filter}
                order by e.id asc
                limit ?
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def _initialize(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("pragma foreign_keys = on")
            conn.executescript(schema_path.read_text(encoding="utf-8"))


def _result_counts(result: str | None) -> tuple[int, int, int]:
    if result == "1-0":
        return 1, 0, 0
    if result == "0-1":
        return 0, 1, 0
    if result in {"1/2-1/2", "1/2", "draw"}:
        return 0, 0, 1
    return 0, 0, 0
