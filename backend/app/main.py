import os
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.ai import (
    DEFAULT_MODEL,
    OpenRouterConfigError,
    extract_first_json_object,
    get_openrouter_api_key,
    run_openrouter_messages,
    run_openrouter_prompt,
)
from app.db import BoardStore
from app.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIConnectivityResponse,
    AIModelOutput,
    BoardData,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRONTEND_DIST = PROJECT_ROOT / "frontend" / "out"
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "pm.db"
AI_HISTORY_WINDOW = 12

load_dotenv(PROJECT_ROOT / ".env")


def resolve_frontend_dist() -> Path:
    env_dist = os.getenv("FRONTEND_DIST")
    return Path(env_dist).resolve() if env_dist else DEFAULT_FRONTEND_DIST


def resolve_db_path() -> Path:
    env_db_path = os.getenv("DB_PATH")
    return Path(env_db_path).resolve() if env_db_path else DEFAULT_DB_PATH


def _build_ai_messages(request: AIChatRequest) -> list[dict[str, str]]:
    history = request.history[-AI_HISTORY_WINDOW:]
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are an assistant for a Kanban project board.\n"
                "Return only a JSON object with this exact shape:\n"
                "{"
                '"assistantMessage":"string",'
                '"boardUpdate":null|{"columns":[{"id":"string","title":"string","cardIds":["string"]}],"cards":{"card-id":{"id":"string","title":"string","details":"string"}}}'
                "}\n"
                "Rules:\n"
                "1) assistantMessage is always required and non-empty.\n"
                "2) Set boardUpdate to null when no board change is needed.\n"
                "3) When boardUpdate is present, return the full updated board."
            ),
        }
    ]
    messages.extend(
        {"role": item.role, "content": item.content}
        for item in history
    )
    messages.append(
        {
            "role": "user",
            "content": json.dumps(
                {
                    "message": request.message,
                    "board": request.board.model_dump(),
                    "history_window_limit": AI_HISTORY_WINDOW,
                }
            ),
        }
    )
    return messages


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

    @app.post("/api/ai/chat", response_model=AIChatResponse)
    async def ai_chat(
        request: AIChatRequest, username: str = Query(default="user")
    ) -> AIChatResponse:
        try:
            api_key = get_openrouter_api_key()
            raw_response = await run_openrouter_messages(
                _build_ai_messages(request),
                api_key=api_key,
            )
            parsed_output = AIModelOutput.model_validate(
                extract_first_json_object(raw_response)
            )
            updated_board = None
            if parsed_output.boardUpdate is not None:
                updated_board = store.save_board(username, parsed_output.boardUpdate)
        except OpenRouterConfigError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(
                status_code=502,
                detail=f"AI response is invalid: {error}",
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=502, detail=f"OpenRouter request failed: {error}"
            ) from error

        return AIChatResponse(
            model=DEFAULT_MODEL,
            assistantMessage=parsed_output.assistantMessage,
            boardUpdated=updated_board is not None,
            board=updated_board,
        )

    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
    return app


app = create_app()
