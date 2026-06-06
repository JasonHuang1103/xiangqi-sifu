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
