import os
import sqlite3
import sys

from xiangqi_sifu.cli import main


def test_cli_accepts_real_engine_path_and_stores_analysis(tmp_path):
    game_path = tmp_path / "game.txt"
    game_path.write_text("H2-E2 B9-C7\n", encoding="utf-8")
    db_path = tmp_path / "analysis.db"
    report_path = tmp_path / "report.md"
    fake_engine = _write_fake_uci_engine(tmp_path)

    exit_code = main(
        [
            "analyze",
            str(game_path),
            "--engine",
            str(fake_engine),
            "--db",
            str(db_path),
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("select count(*) from evaluations").fetchone()[0] == 3
        assert conn.execute("select best_move from evaluations where ply = 0").fetchone()[0] == "h2e2"
    assert "Xiangqi Sifu Review" in report_path.read_text(encoding="utf-8")


def test_cli_can_add_static_verified_explanations(tmp_path):
    game_path = tmp_path / "game.txt"
    game_path.write_text("H2-E2\n", encoding="utf-8")
    db_path = tmp_path / "analysis.db"
    report_path = tmp_path / "report.md"
    fake_engine = _write_fake_swing_engine(tmp_path)

    exit_code = main(
        [
            "analyze",
            str(game_path),
            "--engine",
            str(fake_engine),
            "--db",
            str(db_path),
            "--report",
            str(report_path),
            "--explain",
            "mock",
        ]
    )

    assert exit_code == 0
    report = report_path.read_text(encoding="utf-8")
    assert "## Verified Explanations" in report
    assert "Pikafish prefers `h0g2`" in report
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "select provider, status, confidence, explanation_text from explanations"
        ).fetchone()
    assert row[0] == "static"
    assert row[1] == "PASS"
    assert row[2] == "Medium"
    assert "h0g2" in row[3]


def _write_fake_uci_engine(tmp_path):
    script = tmp_path / "fake_cli_uci_engine.py"
    script.write_text(
        f"""#!{sys.executable}
import sys

for raw in sys.stdin:
    command = raw.strip()
    if command == "uci":
        print("id name Fake CLI Pikafish")
        print("uciok")
        sys.stdout.flush()
    elif command == "isready":
        print("readyok")
        sys.stdout.flush()
    elif command.startswith("go "):
        print("info depth 1 score cp 0 pv h2e2 b9c7")
        print("bestmove h2e2")
        sys.stdout.flush()
    elif command == "quit":
        break
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | os.X_OK)
    return script


def _write_fake_swing_engine(tmp_path):
    script = tmp_path / "fake_swing_uci_engine.py"
    script.write_text(
        f"""#!{sys.executable}
import sys

calls = 0

for raw in sys.stdin:
    command = raw.strip()
    if command == "uci":
        print("id name Fake Swing Pikafish")
        print("uciok")
        sys.stdout.flush()
    elif command == "isready":
        print("readyok")
        sys.stdout.flush()
    elif command.startswith("go "):
        score = 120 if calls == 0 else 80
        best = "h0g2" if calls == 0 else "b9c7"
        print(f"info depth 1 score cp {{score}} pv {{best}} b9c7")
        print(f"bestmove {{best}}")
        calls += 1
        sys.stdout.flush()
    elif command == "quit":
        break
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | os.X_OK)
    return script
