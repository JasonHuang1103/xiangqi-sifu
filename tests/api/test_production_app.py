from fastapi.testclient import TestClient

from xiangqi_sifu.api.main import create_app


def test_production_app_serves_the_built_client(tmp_path):
    frontend = tmp_path / "dist"
    frontend.mkdir()
    (frontend / "index.html").write_text("<main>Scholar's Studio</main>", encoding="utf-8")

    client = TestClient(
        create_app(data_dir=tmp_path / "data", frontend_dir=frontend)
    )

    assert client.get("/").text == "<main>Scholar's Studio</main>"
    assert client.get("/api/health").json()["status"] == "ok"
