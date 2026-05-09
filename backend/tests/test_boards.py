from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import create_app


def test_list_boards_empty() -> None:
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
        response = client.get("/api/boards")

        assert response.status_code == 200
        boards = response.json()
        assert len(boards) >= 1


def test_list_boards_requires_auth() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        response = client.get("/api/boards")

        assert response.status_code == 401


def test_create_board() -> None:
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
        response = client.post("/api/boards?name=Work%20Board")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Work Board"
        assert "id" in data


def test_create_board_requires_auth() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        response = client.post("/api/boards?name=Test")

        assert response.status_code == 401


def test_delete_board() -> None:
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

        response = client.delete(f"/api/boards/{board_id}")

        assert response.status_code == 200


def test_delete_board_not_owner_fails() -> None:
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
        response = client.delete(f"/api/boards/{board_id}")

        assert response.status_code == 404


def test_get_specific_board() -> None:
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

        response = client.get(f"/api/board/{board_id}")

        assert response.status_code == 200
        data = response.json()
        assert "columns" in data
        assert "cards" in data


def test_get_specific_board_not_found() -> None:
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

        response = client.get("/api/board/99999")

        assert response.status_code == 404


def test_update_specific_board() -> None:
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

        board = client.get(f"/api/board/{board_id}").json()
        board["columns"][0]["title"] = "Updated Column"

        response = client.put(f"/api/board/{board_id}", json=board)

        assert response.status_code == 200
        assert response.json()["columns"][0]["title"] == "Updated Column"