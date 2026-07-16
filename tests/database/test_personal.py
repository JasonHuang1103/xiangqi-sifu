import sqlite3

from xiangqi_sifu.config import DEFAULT_START_FEN
from xiangqi_sifu.database.personal import PersonalRepository


AFTER_H2E2 = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR b - - 1 1"


def test_move_is_durable_after_repository_reopens(tmp_path):
    path = tmp_path / "personal.db"
    game = PersonalRepository(path).create_game(mode="friend")

    PersonalRepository(path).append_move(game.id, "h2e2", AFTER_H2E2)
    restored = PersonalRepository(path).get_game(game.id)

    assert restored.status == "active"
    assert restored.current_fen == AFTER_H2E2
    assert [(move.ply, move.uci) for move in restored.moves] == [(1, "h2e2")]


def test_personal_writes_do_not_touch_reference_database(tmp_path):
    reference_path = tmp_path / "reference.db"
    with sqlite3.connect(reference_path) as connection:
        connection.execute("create table sentinel (value text not null)")
        connection.execute("insert into sentinel values ('unchanged')")
    before = reference_path.read_bytes()

    repository = PersonalRepository(tmp_path / "personal.db")
    repository.create_game(mode="sifu", human_side="w", ai_level=5)

    assert reference_path.read_bytes() == before


def test_undo_retracts_latest_move_but_preserves_audit_event(tmp_path):
    repository = PersonalRepository(tmp_path / "personal.db")
    game = repository.create_game(mode="friend")
    repository.append_move(game.id, "h2e2", AFTER_H2E2)

    restored = repository.undo_last_move(game.id)

    assert restored.current_fen == DEFAULT_START_FEN
    assert restored.moves == ()
    with sqlite3.connect(repository.path) as connection:
        retracted = connection.execute(
            "select retracted from moves where game_id = ?", (game.id,)
        ).fetchone()[0]
        event = connection.execute(
            "select event_type from game_events where game_id = ? order by id desc", (game.id,)
        ).fetchone()[0]
    assert retracted == 1
    assert event == "undo"


def test_finish_game_stores_result_and_lists_active_games_first(tmp_path):
    repository = PersonalRepository(tmp_path / "personal.db")
    completed = repository.create_game(mode="friend", red_name="Mei", black_name="Lin")
    active = repository.create_game(mode="sifu", human_side="b", ai_level=7)

    finished = repository.finish_game(completed.id, result="1-0", termination="resignation")
    games = repository.list_games()

    assert finished.status == "completed"
    assert finished.result == "1-0"
    assert finished.termination == "resignation"
    assert [game.id for game in games] == [active.id, completed.id]
