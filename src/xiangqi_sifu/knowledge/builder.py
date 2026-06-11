from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from xiangqi_sifu.board.fen import generate_positions
from xiangqi_sifu.knowledge.repository import KnowledgeBaseRepository


@dataclass(frozen=True)
class BuildSummary:
    games_seen: int
    games_indexed: int
    games_skipped: int
    positions_indexed: int


def build_knowledge_base(
    games_jsonl_paths: Iterable[str | Path],
    db_path: str | Path,
    *,
    corpus_name: str = "public",
    max_games: int | None = None,
    max_examples_per_move: int = 3,
) -> BuildSummary:
    repo = KnowledgeBaseRepository(db_path)
    games_seen = 0
    games_indexed = 0
    games_skipped = 0
    positions_indexed = 0

    with sqlite3.connect(repo.db_path) as conn:
        conn.execute("pragma foreign_keys = on")
        conn.execute("pragma synchronous = normal")
        _reset_stage(conn)
        for path in games_jsonl_paths:
            source_path = Path(path)
            with source_path.open("r", encoding="utf-8") as source:
                for line in source:
                    if max_games is not None and games_seen >= max_games:
                        break
                    if not line.strip():
                        continue
                    games_seen += 1
                    record = json.loads(line)
                    try:
                        positions_indexed += _stage_record(
                            repo,
                            conn,
                            record,
                            corpus_name=corpus_name,
                            source_file=source_path.as_posix(),
                        )
                    except (KeyError, ValueError):
                        games_skipped += 1
                        continue
                    games_indexed += 1
            if max_games is not None and games_seen >= max_games:
                break
        _aggregate_stage(conn, max_examples_per_move=max_examples_per_move)
        conn.execute("drop table if exists kb_move_occurrences_stage")

    return BuildSummary(
        games_seen=games_seen,
        games_indexed=games_indexed,
        games_skipped=games_skipped,
        positions_indexed=positions_indexed,
    )


def _reset_stage(conn: sqlite3.Connection) -> None:
    conn.execute("drop table if exists kb_move_occurrences_stage")
    conn.execute(
        """
        create table kb_move_occurrences_stage (
            fen text not null,
            side_to_move text not null,
            move_uci text not null,
            move_iccs text not null,
            side text not null,
            red_win integer not null,
            black_win integer not null,
            draw integer not null,
            game_id integer not null,
            ply integer not null
        )
        """
    )


def _stage_record(
    repo: KnowledgeBaseRepository,
    conn: sqlite3.Connection,
    record: dict,
    *,
    corpus_name: str,
    source_file: str,
) -> int:
    moves = record["moves"]
    move_uci = [move["uci"] for move in moves]
    positions = generate_positions(record["starting_fen"], move_uci)
    game_id = repo.save_game_in_connection(
        conn,
        record,
        corpus_name=corpus_name,
        source_file=source_file,
    )

    red_win, black_win, draw = _result_counts(record.get("result"))
    stage_rows = []
    for index, move in enumerate(moves):
        before = positions[index]
        stage_rows.append(
            (
                before.fen,
                before.side_to_move,
                move["uci"],
                move["iccs"],
                move["side"],
                red_win,
                black_win,
                draw,
                game_id,
                int(move["ply"]),
            )
        )
    conn.executemany(
        """
        insert into kb_move_occurrences_stage (
            fen, side_to_move, move_uci, move_iccs, side,
            red_win, black_win, draw, game_id, ply
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        stage_rows,
    )
    return len(stage_rows)


def _aggregate_stage(
    conn: sqlite3.Connection,
    *,
    max_examples_per_move: int,
) -> None:
    conn.execute(
        """
        insert into kb_positions (fen, side_to_move, occurrence_count)
        select fen, min(side_to_move), count(*)
        from kb_move_occurrences_stage
        group by fen
        on conflict(fen) do update set
            occurrence_count = occurrence_count + excluded.occurrence_count
        """
    )
    conn.execute(
        """
        insert into kb_moves (
            fen, move_uci, move_iccs, side, play_count,
            red_wins, black_wins, draws, sample_game_id, sample_ply
        )
        select
            fen,
            move_uci,
            min(move_iccs),
            min(side),
            count(*),
            sum(red_win),
            sum(black_win),
            sum(draw),
            min(game_id),
            min(ply)
        from kb_move_occurrences_stage
        group by fen, move_uci
        on conflict(fen, move_uci) do update set
            play_count = play_count + excluded.play_count,
            red_wins = red_wins + excluded.red_wins,
            black_wins = black_wins + excluded.black_wins,
            draws = draws + excluded.draws
        """
    )
    if max_examples_per_move <= 0:
        return
    conn.execute(
        """
        insert or ignore into kb_examples (fen, move_uci, game_id, ply)
        select fen, move_uci, game_id, ply
        from (
            select
                fen,
                move_uci,
                game_id,
                ply,
                row_number() over (
                    partition by fen, move_uci
                    order by game_id, ply
                ) as example_rank
            from kb_move_occurrences_stage
        )
        where example_rank <= ?
        """,
        (max_examples_per_move,),
    )


def _result_counts(result: str | None) -> tuple[int, int, int]:
    if result == "1-0":
        return 1, 0, 0
    if result == "0-1":
        return 0, 1, 0
    if result in {"1/2-1/2", "1/2", "draw"}:
        return 0, 0, 1
    return 0, 0, 0
