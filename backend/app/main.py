import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.ai import (
    DEFAULT_MODEL,
    OpenRouterConfigError,
    get_openrouter_api_key,
    run_openrouter_prompt,
)
from app.db import BoardStore
from app.schemas import AIConnectivityResponse, BoardData

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRONTEND_DIST = PROJECT_ROOT / "frontend" / "out"
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "pm.db"

load_dotenv(PROJECT_ROOT / ".env")


def resolve_frontend_dist() -> Path:
    env_dist = os.getenv("FRONTEND_DIST")
    return Path(env_dist).resolve() if env_dist else DEFAULT_FRONTEND_DIST


def resolve_db_path() -> Path:
    env_db_path = os.getenv("DB_PATH")
    return Path(env_db_path).resolve() if env_db_path else DEFAULT_DB_PATH


def create_app(frontend_dist: Path | None = None, db_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="PM MVP Backend")
    dist_dir = frontend_dist or resolve_frontend_dist()
    store = BoardStore(db_path or resolve_db_path())
    store.initialize()

    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        raise RuntimeError(
            f"Frontend build output not found at {dist_dir}. "
            "Build frontend static assets with `npm run build` in frontend/."
        )

    @app.get("/api/hello")
    async def hello() -> dict[str, str]:
        return {"message": "hello world"}

    @app.get("/api/board", response_model=BoardData)
    async def get_board(username: str = Query(default="user")) -> BoardData:
        try:
            return store.get_board(username)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.put("/api/board", response_model=BoardData)
    async def update_board(
        board: BoardData, username: str = Query(default="user")
    ) -> BoardData:
        try:
            return store.save_board(username, board)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/ai/connectivity", response_model=AIConnectivityResponse)
    async def ai_connectivity_check() -> AIConnectivityResponse:
        prompt = "2+2"
        try:
            api_key = get_openrouter_api_key()
            response_text = await run_openrouter_prompt(prompt, api_key=api_key)
        except OpenRouterConfigError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(
                status_code=502, detail=f"OpenRouter request failed: {error}"
            ) from error
        return AIConnectivityResponse(
            model=DEFAULT_MODEL,
            prompt=prompt,
            response=response_text,
        )

    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
    return app


app = create_app()
