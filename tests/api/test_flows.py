from fastapi.testclient import TestClient

from xiangqi_sifu.analysis.models import EngineLine
from xiangqi_sifu.api.main import create_app
from xiangqi_sifu.config import DEFAULT_START_FEN


class FakeEngine:
    def analyze_lines(self, position, *, multipv=3):
        return (
            EngineLine(1, 120, None, "h2e2", ("h2e2", "b9c7"), 8, 1000),
            EngineLine(2, 80, None, "h0g2", ("h0g2", "b9c7"), 8, 900),
        )[:multipv]


def client(tmp_path):
    return TestClient(create_app(data_dir=tmp_path, engine=FakeEngine()))


def test_position_validation_and_analysis_flow(tmp_path):
    api = client(tmp_path)
    pieces = api.post("/api/positions/validate", json={"fen": DEFAULT_START_FEN}).json()["pieces"]

    response = api.post(
        "/api/analysis/positions",
        json={"fen": DEFAULT_START_FEN, "multipv": 2},
    )

    assert response.status_code == 200
    assert len(pieces) == 32
    assert response.json()["lines"][0]["best_move"] == "h2e2"
    assert response.json()["lines"][0]["estimated_red_win_rate"] > 0.5


def test_record_inspection_flow(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/api/records/inspect",
        json={"text": "[Event \"Club\"]\n[Red \"Mei\"]\n1. H2-E2 B9-C7"},
    )

    assert response.status_code == 200
    assert response.json()["total_games"] == 1
    assert response.json()["games"][0]["red"] == "Mei"


def test_selected_game_can_be_analyzed_move_by_move(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/api/analysis/games",
        json={"starting_fen": DEFAULT_START_FEN, "moves": ["h2e2"], "multipv": 1},
    )

    assert response.status_code == 200
    assert [row["ply"] for row in response.json()["positions"]] == [0, 1]
    assert response.json()["positions"][1]["played_move"] == "h2e2"


def test_game_review_can_analyze_only_the_selected_ply(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/api/analysis/games",
        json={
            "starting_fen": DEFAULT_START_FEN,
            "moves": ["h2e2", "b9c7"],
            "multipv": 1,
            "selected_ply": 1,
        },
    )

    assert response.status_code == 200
    assert [len(row["lines"]) for row in response.json()["positions"]] == [0, 1, 0]


def test_friend_game_move_is_legal_and_persisted(tmp_path):
    api = client(tmp_path)
    created = api.post("/api/play/games", json={"mode": "friend"}).json()

    moved = api.post(f"/api/play/games/{created['id']}/moves", json={"uci": "h2e2"})
    restored = api.get(f"/api/personal/games/{created['id']}")

    assert moved.status_code == 200
    assert moved.json()["moves"][0]["uci"] == "h2e2"
    assert restored.json()["current_fen"] == moved.json()["current_fen"]
    assert restored.json()["side_to_move"] == "black"


def test_sifu_move_uses_engine_candidate_and_persists_it(tmp_path):
    api = client(tmp_path)
    created = api.post(
        "/api/play/games",
        json={"mode": "sifu", "human_side": "b", "ai_level": 10},
    ).json()

    response = api.post(f"/api/play/games/{created['id']}/ai-move")

    assert response.status_code == 200
    assert response.json()["moves"][0]["uci"] == "h2e2"


def test_coach_thread_persists_grounded_conversation(tmp_path):
    api = client(tmp_path)
    thread = api.post(
        "/api/coach/threads",
        json={
            "fen": DEFAULT_START_FEN,
            "side_to_move": "red",
            "best_move": "h2e2",
            "red_score_cp": 120,
            "pv": ["h2e2", "b9c7"],
        },
    ).json()

    response = api.post(
        f"/api/coach/threads/{thread['id']}/messages",
        json={"question": "Why this move?"},
    )

    assert response.status_code == 200
    assert "h2e2" in response.json()["reply"]["text"]
    assert [message["role"] for message in response.json()["messages"]] == ["user", "assistant"]
