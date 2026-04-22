import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRONTEND_DIST = PROJECT_ROOT / "frontend" / "out"


def resolve_frontend_dist() -> Path:
    env_dist = os.getenv("FRONTEND_DIST")
    return Path(env_dist).resolve() if env_dist else DEFAULT_FRONTEND_DIST


def create_app(frontend_dist: Path | None = None) -> FastAPI:
    app = FastAPI(title="PM MVP Backend")
    dist_dir = frontend_dist or resolve_frontend_dist()

    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        raise RuntimeError(
            f"Frontend build output not found at {dist_dir}. "
            "Build frontend static assets with `npm run build` in frontend/."
        )

    @app.get("/api/hello")
    async def hello() -> dict[str, str]:
        return {"message": "hello world"}

    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
    return app


app = create_app()
