from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import create_app


def test_root_serves_frontend_index() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir)
        db_path = dist / "test.db"
        (dist / "index.html").write_text(
            "<!doctype html><html><body><h1>Kanban Studio</h1></body></html>",
            encoding="utf-8",
        )
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Kanban Studio" in response.text


def test_api_hello_returns_expected_payload() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir)
        db_path = dist / "test.db"
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}
