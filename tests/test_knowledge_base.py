import json
import sqlite3

from xiangqi_sifu.config import DEFAULT_START_FEN
from scripts.build_knowledge_base import main as build_kb_main
from scripts.query_knowledge_base import main as query_kb_main
from xiangqi_sifu.knowledge.builder import build_knowledge_base
from xiangqi_sifu.knowledge.repository import KnowledgeBaseRepository


def test_build_knowledge_base_indexes_position_move_stats(tmp_path):
    games_path = tmp_path / "games.jsonl"
    db_path = tmp_path / "knowledge.db"
    games_path.write_text(
        "\n".join(
            [
                json.dumps(_game_record(1, "1-0", ["H2-E2", "B9-C7"])),
                json.dumps(_game_record(2, "1/2-1/2", ["H2-E2", "H9-G7"])),
                json.dumps(_game_record(3, "0-1", ["H0-G2", "B9-C7"])),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = build_knowledge_base(
        [games_path],
        db_path,
        corpus_name="sample",
        max_examples_per_move=2,
    )

    assert summary.games_indexed == 3
    assert summary.games_skipped == 0
    repo = KnowledgeBaseRepository(db_path)
    moves = repo.get_position_moves(DEFAULT_START_FEN)

    assert moves[0]["move_uci"] == "h2e2"
    assert moves[0]["play_count"] == 2
    assert moves[0]["red_wins"] == 1
    assert moves[0]["draws"] == 1
    assert moves[0]["black_wins"] == 0
    assert moves[1]["move_uci"] == "h0g2"
    assert moves[1]["play_count"] == 1
    assert repo.get_position_summary(DEFAULT_START_FEN)["occurrence_count"] == 3

    examples = repo.get_representative_games(DEFAULT_START_FEN, "h2e2")
    assert len(examples) == 2
    assert examples[0]["red"] == "Red 1"
    assert examples[0]["ply"] == 1


def test_knowledge_base_repository_returns_empty_for_unknown_position(tmp_path):
    repo = KnowledgeBaseRepository(tmp_path / "knowledge.db")

    assert repo.get_position_summary("unknown fen") is None
    assert repo.get_position_moves("unknown fen") == []
    assert repo.get_representative_games("unknown fen") == []


def test_build_knowledge_base_uses_bulk_aggregation_path(tmp_path, monkeypatch):
    games_path = tmp_path / "games.jsonl"
    db_path = tmp_path / "knowledge.db"
    games_path.write_text(
        "\n".join(
            [
                json.dumps(_game_record(1, "1-0", ["H2-E2", "B9-C7"])),
                json.dumps(_game_record(2, "0-1", ["H0-G2", "B9-C7"])),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_row_upsert(*args, **kwargs):
        raise AssertionError("knowledge-base builds should aggregate staged rows in bulk")

    monkeypatch.setattr(
        KnowledgeBaseRepository,
        "add_position_move_in_connection",
        fail_row_upsert,
    )

    summary = build_knowledge_base([games_path], db_path)

    assert summary.games_indexed == 2
    assert summary.positions_indexed == 4
    assert KnowledgeBaseRepository(db_path).get_position_summary(DEFAULT_START_FEN)[
        "occurrence_count"
    ] == 2


def test_build_and_query_knowledge_base_scripts(tmp_path, capsys):
    games_path = tmp_path / "games.jsonl"
    db_path = tmp_path / "knowledge.db"
    games_path.write_text(
        json.dumps(_game_record(1, "1-0", ["H2-E2", "B9-C7"])) + "\n",
        encoding="utf-8",
    )

    build_exit = build_kb_main([str(games_path), "--db", str(db_path)])
    query_exit = query_kb_main(["--db", str(db_path), "--fen", DEFAULT_START_FEN])

    captured = capsys.readouterr()
    assert build_exit == 0
    assert query_exit == 0
    assert "Games indexed: 1" in captured.out
    assert '"move_uci": "h2e2"' in captured.out


def _game_record(game_id: int, result: str, moves: list[str]) -> dict:
    return {
        "schema_version": 1,
        "game_id": game_id,
        "metadata": {"Event": f"Game {game_id}"},
        "red": f"Red {game_id}",
        "black": f"Black {game_id}",
        "result": result,
        "starting_fen": DEFAULT_START_FEN,
        "move_count": len(moves),
        "moves": [
            {
                "ply": index + 1,
                "move_number": (index // 2) + 1,
                "side": "red" if index % 2 == 0 else "black",
                "iccs": move,
                "uci": move.replace("-", "").lower(),
            }
            for index, move in enumerate(moves)
        ],
    }
