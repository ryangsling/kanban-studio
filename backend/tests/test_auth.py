from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import create_app


def test_register_user() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
        assert "session_token" in client.cookies


def test_register_duplicate_user_fails() -> None:
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
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password456"},
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


def test_login_existing_user() -> None:
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
        client.cookies.clear()
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "session_token" in client.cookies


def test_login_invalid_credentials() -> None:
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
        client.cookies.clear()
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401


def test_get_current_user() -> None:
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
        response = client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


def test_get_current_user_unauthenticated() -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        response = client.get("/api/auth/me")

        assert response.status_code == 401


def test_logout() -> None:
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
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        me_response = client.get("/api/auth/me")
        assert me_response.status_code == 401