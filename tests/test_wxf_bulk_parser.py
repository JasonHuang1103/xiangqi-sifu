import json

from xiangqi_sifu.parsers.wxf_bulk_parser import iter_game_texts, write_games_jsonl


SAMPLE_TWO_GAMES = """[Game "Chinese Chess"]
[Event "First"]
[Red "A"]
[Black "B"]
[Result "1-0"]
[Format "ICCS"]
1. H2-E2 B9-C7
1-0

[Game "Chinese Chess"]
[Event "Second"]
[Red "C"]
[Black "D"]
[Result "0-1"]
[Format "ICCS"]
1. C3-C4 H9-G7
0-1
"""


def test_iter_game_texts_splits_on_chinese_chess_game_tag(tmp_path):
    source = tmp_path / "sample.pgns"
    source.write_text(SAMPLE_TWO_GAMES, encoding="utf-8")

    games = list(iter_game_texts(source))

    assert len(games) == 2
    assert games[0].startswith('[Game "Chinese Chess"]')
    assert '[Event "First"]' in games[0]
    assert '[Event "Second"]' not in games[0]
    assert '[Event "Second"]' in games[1]


def test_write_games_jsonl_exports_one_record_per_game(tmp_path):
    source = tmp_path / "sample.pgns"
    output_dir = tmp_path / "processed"
    source.write_text(SAMPLE_TWO_GAMES, encoding="utf-8")

    summary = write_games_jsonl(source, output_dir)

    assert summary.game_count == 2
    assert summary.output_path == output_dir / "games.jsonl"
    assert summary.manifest_path == output_dir / "manifest.json"

    records = [
        json.loads(line)
        for line in summary.output_path.read_text(encoding="utf-8").splitlines()
    ]
    assert records[0]["game_id"] == 1
    assert records[0]["metadata"]["Event"] == "First"
    assert records[0]["red"] == "A"
    assert records[0]["black"] == "B"
    assert records[0]["move_count"] == 2
    assert records[0]["moves"][0] == {
        "ply": 1,
        "move_number": 1,
        "side": "red",
        "iccs": "H2-E2",
        "uci": "h2e2",
    }
    assert records[1]["game_id"] == 2
    assert records[1]["metadata"]["Event"] == "Second"

    manifest = json.loads(summary.manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_file"] == str(source)
    assert manifest["game_count"] == 2
    assert manifest["format"] == "jsonl"
