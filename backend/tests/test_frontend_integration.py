from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_OUT_DIR = PROJECT_ROOT / "frontend" / "out"


def test_built_frontend_is_served_at_root() -> None:
    assert FRONTEND_OUT_DIR.exists(), (
        "frontend/out is missing. Run `npm run build` in frontend/ before backend tests."
    )

    client = TestClient(create_app(frontend_dist=FRONTEND_OUT_DIR))
    response = client.get("/")

    assert response.status_code == 200
    assert "Sign in" in response.text
    assert "PM MVP Access" in response.text
