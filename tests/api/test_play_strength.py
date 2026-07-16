from fastapi.testclient import TestClient

from xiangqi_sifu.analysis.models import EngineLine
from xiangqi_sifu.api.main import create_app


class RankedEngine:
    def analyze_lines(self, position, *, multipv=3):
        moves = ("h2e2", "h0g2", "b0c2", "c3c4", "g3g4")
        return tuple(
            EngineLine(rank, 100 - rank * 20, None, move, (move,), 6, 100)
            for rank, move in enumerate(moves[:multipv], start=1)
        )


def test_level_ten_always_chooses_the_first_engine_line(tmp_path):
    api = TestClient(create_app(data_dir=tmp_path, engine=RankedEngine()))
    game = api.post(
        "/api/play/games",
        json={"mode": "sifu", "human_side": "b", "ai_level": 10},
    ).json()

    moved = api.post(f"/api/play/games/{game['id']}/ai-move")

    assert moved.status_code == 200
    assert moved.json()["moves"][0]["uci"] == "h2e2"


def test_level_one_chooses_a_legal_multipv_candidate(tmp_path):
    api = TestClient(create_app(data_dir=tmp_path, engine=RankedEngine()))
    game = api.post(
        "/api/play/games",
        json={"mode": "sifu", "human_side": "b", "ai_level": 1},
    ).json()

    moved = api.post(f"/api/play/games/{game['id']}/ai-move")

    assert moved.status_code == 200
    assert moved.json()["moves"][0]["uci"] in {"h2e2", "h0g2", "b0c2", "c3c4", "g3g4"}
    assert moved.json()["moves"][0]["uci"] != "h2e2"


def test_adaptive_level_changes_by_at_most_one_after_a_game(tmp_path):
    api = TestClient(create_app(data_dir=tmp_path, engine=RankedEngine()))
    game = api.post(
        "/api/play/games",
        json={"mode": "sifu", "human_side": "w", "adaptive": True},
    ).json()
    assert game["ai_level"] == 5
    assert game["ai_adaptive"] is True

    api.post(f"/api/play/games/{game['id']}/resign", json={"side": "b"})
    next_game = api.post(
        "/api/play/games",
        json={"mode": "sifu", "human_side": "w", "adaptive": True},
    ).json()

    assert next_game["ai_level"] == 6
