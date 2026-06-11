import importlib.util
import os
import sqlite3
import sys
from pathlib import Path


def test_run_review_with_mock_engine_returns_tables_and_persists_db(tmp_path):
    app = _load_streamlit_app_module()
    db_path = tmp_path / "streamlit_review.db"

    review = app.run_review_from_text(
        "H2-E2 B9-C7\nH0-G2",
        engine_value="mock",
        db_path=db_path,
        depth=4,
    )

    assert review.game_id == 1
    assert [row["played"] for row in review.move_rows] == ["h2e2", "b9c7", "h0g2"]
    assert [row["ply"] for row in review.eval_rows] == [0, 1, 2, 3]
    assert review.impact_rows[0]["red_delta_cp"] == 0
    assert review.impact_rows[0]["mover_loss_cp"] == 0
    assert review.mistake_rows == []
    assert "# Xiangqi Sifu Review" in review.report_markdown

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("select count(*) from games").fetchone()[0] == 1
        assert conn.execute("select count(*) from evaluations").fetchone()[0] == 4


def test_run_review_can_generate_and_store_mock_explanations(tmp_path):
    app = _load_streamlit_app_module()
    db_path = tmp_path / "streamlit_review.db"

    review = app.run_review_from_text(
        "H2-E2",
        engine_value=str(_write_fake_swing_engine(tmp_path)),
        db_path=db_path,
        depth=4,
        explanation_provider="mock",
        thresholds=app.MistakeThresholds(inaccuracy_cp=1, mistake_cp=2, blunder_cp=3),
    )

    assert review.explanation_rows
    assert review.explanation_rows[0]["status"] == "PASS"
    assert review.explanation_rows[0]["confidence"] == "Medium"
    assert "## Verified Explanations" in review.report_markdown
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("select count(*) from explanations").fetchone()[0] == 1


def test_parse_uploaded_text_accepts_bytes():
    app = _load_streamlit_app_module()

    assert app.decode_uploaded_bytes(b"H2-E2 B9-C7") == "H2-E2 B9-C7"


def _write_fake_swing_engine(tmp_path):
    script = tmp_path / "fake_streamlit_uci_engine.py"
    script.write_text(
        f"""#!{sys.executable}
import sys

calls = 0

for raw in sys.stdin:
    command = raw.strip()
    if command == "uci":
        print("id name Fake Streamlit Pikafish")
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


def _load_streamlit_app_module():
    path = Path(__file__).resolve().parents[1] / "frontend" / "streamlit_app.py"
    spec = importlib.util.spec_from_file_location("streamlit_app", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
