from fastapi.testclient import TestClient

from xiangqi_sifu.api.main import create_app


def test_health_describes_local_runtime(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path, engine_path=None))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "engine_available": False,
        "personal_db": str(tmp_path / "personal.db"),
        "reference_db": str(tmp_path / "reference.db"),
    }
