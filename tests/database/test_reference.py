import json
import sqlite3

import pytest

from xiangqi_sifu.database.reference import ReferenceRepository


def test_reference_search_and_game_loading_are_read_only(tmp_path):
    jsonl = tmp_path / "games.jsonl"
    record = {
        "game_id": 1,
        "metadata": {"Event": "Masters Cup"},
        "red": "Hu Ronghua",
        "black": "Liu Dahua",
        "result": "1-0",
        "starting_fen": "start",
        "move_count": 1,
        "moves": [{"ply": 1, "uci": "h2e2", "iccs": "H2-E2", "side": "red"}],
    }
    jsonl.write_text(json.dumps(record) + "\n", encoding="utf-8")
    database = tmp_path / "reference.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            create table kb_games (
                id integer primary key, corpus_name text, source_file text,
                source_game_id integer, event text, red text, black text,
                result text, starting_fen text, move_count integer, metadata_json text
            )
            """
        )
        connection.execute(
            "insert into kb_games values (1, 'public', ?, 1, 'Masters Cup', 'Hu Ronghua', "
            "'Liu Dahua', '1-0', 'start', 1, '{}')",
            (str(jsonl),),
        )
    before = database.read_bytes()
    repository = ReferenceRepository(database)

    page = repository.search_games("Ronghua", offset=0, limit=20)
    loaded = repository.get_game(1)

    assert page.total == 1
    assert page.games[0].event == "Masters Cup"
    assert loaded.record["moves"][0]["uci"] == "h2e2"
    assert database.read_bytes() == before
    with pytest.raises(sqlite3.OperationalError):
        with repository.connect() as connection:
            connection.execute("delete from kb_games")
