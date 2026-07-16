import pytest

from xiangqi_sifu.records.service import RecordInspectionError, inspect_record


TWO_GAMES = """[Game "Chinese Chess"]
[Event "First"]
[Red "A"]
[Black "B"]
[Result "1-0"]
1. H2-E2 B9-C7
1-0

[Game "Chinese Chess"]
[Event "Second"]
[Red "C"]
[Black "D"]
[Result "0-1"]
1. C3-C4 H9-G7
0-1
"""


def test_inspect_single_record_opens_directly():
    inspection = inspect_record("1. H2-E2 B9-C7")

    assert inspection.total_games == 1
    assert inspection.requires_selection is False
    assert inspection.games[0].move_count == 2


def test_inspect_multi_game_record_returns_paginated_summaries():
    inspection = inspect_record(TWO_GAMES, offset=1, limit=1)

    assert inspection.total_games == 2
    assert inspection.requires_selection is True
    assert len(inspection.games) == 1
    assert inspection.games[0].index == 1
    assert inspection.games[0].event == "Second"
    assert inspection.games[0].red == "C"


def test_inspect_record_identifies_game_and_bad_token():
    text = TWO_GAMES.replace("C3-C4", "NOT-A-MOVE")

    with pytest.raises(RecordInspectionError) as error:
        inspect_record(text)

    assert error.value.game_index == 1
    assert "NOT-A-MOVE" in error.value.detail
