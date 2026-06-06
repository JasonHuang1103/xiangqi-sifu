import importlib.util
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


def test_parse_uploaded_text_accepts_bytes():
    app = _load_streamlit_app_module()

    assert app.decode_uploaded_bytes(b"H2-E2 B9-C7") == "H2-E2 B9-C7"


def _load_streamlit_app_module():
    path = Path(__file__).resolve().parents[1] / "frontend" / "streamlit_app.py"
    spec = importlib.util.spec_from_file_location("streamlit_app", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
