from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import create_app


def test_rename_board() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        boards = client.get("/api/boards").json()
        board_id = boards[0]["id"]

        response = client.patch(f"/api/boards/{board_id}?name=Renamed%20Board")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed Board"

        # Verify it's renamed in the list
        updated_boards = client.get("/api/boards").json()
        assert any(b["name"] == "Renamed Board" for b in updated_boards)


def test_rename_board_empty_name_fails() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        boards = client.get("/api/boards").json()
        board_id = boards[0]["id"]

        response = client.patch(f"/api/boards/{board_id}?name=")

        assert response.status_code == 400


def test_rename_board_not_owner_fails() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        client.post(
            "/api/auth/register",
            json={"username": "user1", "password": "password123"},
        )
        boards = client.get("/api/boards").json()
        board_id = boards[0]["id"]

        client.post(
            "/api/auth/register",
            json={"username": "user2", "password": "password456"},
        )
        response = client.patch(f"/api/boards/{board_id}?name=Hacked")

        assert response.status_code == 404