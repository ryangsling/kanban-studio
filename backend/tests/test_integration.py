"""Integration tests covering the full user flow."""
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import create_app


def test_full_user_flow_register_login_boards() -> None:
    """Test the complete user flow: register -> login -> create boards -> manage cards."""
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        # 1. Register a new user
        register_resp = client.post(
            "/api/auth/register",
            json={"username": "alice", "password": "secret123"},
        )
        assert register_resp.status_code == 200
        assert register_resp.json()["username"] == "alice"

        # 2. Check we can get current user (session works)
        me_resp = client.get("/api/auth/me")
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "alice"

        # 3. List boards (should have default board)
        boards_resp = client.get("/api/boards")
        assert boards_resp.status_code == 200
        boards = boards_resp.json()
        assert len(boards) >= 1
        default_board_id = boards[0]["id"]

        # 4. Get the default board
        board_resp = client.get(f"/api/board/{default_board_id}")
        assert board_resp.status_code == 200
        board = board_resp.json()
        assert len(board["columns"]) > 0
        assert len(board["cards"]) > 0

        # 5. Create a new board
        new_board_resp = client.post("/api/boards?name=Project%20Alpha")
        assert new_board_resp.status_code == 200
        new_board_id = new_board_resp.json()["id"]

        # 6. Verify new board has seed data
        new_board_resp = client.get(f"/api/board/{new_board_id}")
        assert new_board_resp.status_code == 200
        new_board = new_board_resp.json()
        assert len(new_board["columns"]) > 0

        # 7. Update the new board (add a card)
        new_board["columns"][0]["cardIds"].append("card-new")
        new_board["cards"]["card-new"] = {
            "id": "card-new",
            "title": "New Task",
            "details": "This is a new task",
        }
        update_resp = client.put(f"/api/board/{new_board_id}", json=new_board)
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert "card-new" in updated["columns"][0]["cardIds"]

        # 8. Logout
        logout_resp = client.post("/api/auth/logout")
        assert logout_resp.status_code == 200

        # 9. Verify logged out
        me_resp = client.get("/api/auth/me")
        assert me_resp.status_code == 401

        # 10. Can't access boards when logged out
        boards_resp = client.get("/api/boards")
        assert boards_resp.status_code == 401


def test_multi_user_isolation() -> None:
    """Test that users cannot see or modify each other's boards."""
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        # Create user1 and their board
        client.post(
            "/api/auth/register",
            json={"username": "user1", "password": "password1"},
        )
        user1_boards = client.get("/api/boards").json()
        user1_board_id = user1_boards[0]["id"]

        # Create user2
        client.post(
            "/api/auth/register",
            json={"username": "user2", "password": "password2"},
        )

        # User2 should not see user1's board
        user2_boards = client.get("/api/boards").json()
        assert all(b["id"] != user1_board_id for b in user2_boards)

        # User2 cannot access user1's board
        access_resp = client.get(f"/api/board/{user1_board_id}")
        assert access_resp.status_code == 404

        # User2 cannot delete user1's board
        delete_resp = client.delete(f"/api/boards/{user1_board_id}")
        assert delete_resp.status_code == 404

        # User1 still has their board
        client.cookies.clear()
        client.post(
            "/api/auth/login",
            json={"username": "user1", "password": "password1"},
        )
        user1_boards_after = client.get("/api/boards").json()
        assert any(b["id"] == user1_board_id for b in user1_boards_after)


def test_session_persistence() -> None:
    """Test that session persists across requests."""
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        # Register
        client.post(
            "/api/auth/register",
            json={"username": "bob", "password": "secret"},
        )

        # Multiple requests should all work with same session
        for _ in range(3):
            me = client.get("/api/auth/me")
            assert me.status_code == 200
            boards = client.get("/api/boards")
            assert boards.status_code == 200


def test_login_invalidates_old_session() -> None:
    """Test that logging in creates a new session."""
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))

        # Register and get first session token
        client.post(
            "/api/auth/register",
            json={"username": "carol", "password": "password"},
        )
        first_token = client.cookies.get("session_token")

        # Logout
        client.post("/api/auth/logout")

        # Login again
        client.post(
            "/api/auth/login",
            json={"username": "carol", "password": "password"},
        )
        second_token = client.cookies.get("session_token")

        # Tokens should be different
        assert first_token != second_token