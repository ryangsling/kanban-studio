from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import create_app


def test_get_board_returns_seeded_board() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        response = client.get("/api/board")
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["columns"]) == 5
        assert payload["columns"][0]["id"] == "col-backlog"
        assert "card-1" in payload["cards"]


def test_put_board_persists_changes() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        board = client.get("/api/board").json()
        board["columns"][0]["title"] = "Ideas"
        board["columns"][0]["cardIds"].append("card-new")
        board["cards"]["card-new"] = {
            "id": "card-new",
            "title": "Persist from API",
            "details": "Inserted through update endpoint.",
        }

        update_response = client.put("/api/board", json=board)
        next_board = client.get("/api/board").json()

        assert update_response.status_code == 200
        assert next_board["columns"][0]["title"] == "Ideas"
        assert "card-new" in next_board["columns"][0]["cardIds"]
        assert next_board["cards"]["card-new"]["title"] == "Persist from API"
