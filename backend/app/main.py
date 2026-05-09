import os
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.ai import (
    DEFAULT_MODEL,
    OpenRouterConfigError,
    extract_first_json_object,
    get_openrouter_api_key,
    run_openrouter_messages,
    run_openrouter_prompt,
)
from app.db import BoardStore, _now_iso
from app.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIConnectivityResponse,
    AIModelOutput,
    BoardData,
    BoardListItem,
    UserCreate,
    UserLogin,
    UserResponse,
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    dist_dir = frontend_dist or resolve_frontend_dist()
    store = BoardStore(db_path or resolve_db_path())
    store.initialize()

    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        raise RuntimeError(
            f"Frontend build output not found at {dist_dir}. "
            "Build frontend static assets with `npm run build` in frontend/."
        )

    SESSION_COOKIE_NAME = "session_token"

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

    def _get_session_user(request: Request) -> dict | None:
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            return None
        return store.get_user_from_session(token)

    @app.post("/api/auth/register", response_model=UserResponse)
    async def register(response: Response, user_data: UserCreate) -> UserResponse:
        try:
            user = store.create_user(user_data.username, user_data.password)
            token = store.create_session(user["id"])
            response.set_cookie(
                SESSION_COOKIE_NAME,
                token,
                httponly=True,
                samesite="lax",
                max_age=86400,
            )
            return UserResponse(id=user["id"], username=user["username"])
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/auth/login", response_model=UserResponse)
    async def login(response: Response, credentials: UserLogin) -> UserResponse:
        try:
            user = store.authenticate_user(credentials.username, credentials.password)
            token = store.create_session(user["id"])
            response.set_cookie(
                SESSION_COOKIE_NAME,
                token,
                httponly=True,
                samesite="lax",
                max_age=86400,
            )
            return UserResponse(id=user["id"], username=user["username"])
        except ValueError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error

    @app.post("/api/auth/logout")
    async def logout(response: Response, request: Request) -> dict:
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if token:
            store.delete_session(token)
        response.delete_cookie(SESSION_COOKIE_NAME)
        return {"message": "Logged out"}

    @app.get("/api/auth/me", response_model=UserResponse)
    async def get_current_user(request: Request) -> UserResponse:
        user = _get_session_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return UserResponse(id=user["id"], username=user["username"])

    @app.get("/api/boards", response_model=list[BoardListItem])
    async def list_boards(request: Request) -> list[BoardListItem]:
        user = _get_session_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        with store._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, name, created_at, updated_at
                FROM boards
                WHERE owner_user_id = ?
                ORDER BY updated_at DESC
                """,
                (user["id"],),
            ).fetchall()
        return [BoardListItem(id=row["id"], name=row["name"], created_at=row["created_at"], updated_at=row["updated_at"]) for row in rows]

    @app.post("/api/boards", response_model=BoardListItem)
    async def create_board(request: Request, name: str = "My Board") -> BoardListItem:
        user = _get_session_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Board name cannot be empty")
        board = store.create_board_for_user(user["id"], name.strip())
        return BoardListItem(**board)

    @app.delete("/api/boards/{board_id}")
    async def delete_board(request: Request, board_id: int) -> dict:
        user = _get_session_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        with store._connection() as conn:
            result = conn.execute(
                "DELETE FROM boards WHERE id = ? AND owner_user_id = ?",
                (board_id, user["id"]),
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Board not found")
        return {"message": "Board deleted"}

    @app.patch("/api/boards/{board_id}", response_model=BoardListItem)
    async def rename_board(request: Request, board_id: int, name: str) -> BoardListItem:
        user = _get_session_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Board name cannot be empty")
        now = _now_iso()
        with store._connection() as conn:
            result = conn.execute(
                "UPDATE boards SET name = ?, updated_at = ? WHERE id = ? AND owner_user_id = ?",
                (name.strip(), now, board_id, user["id"]),
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Board not found")
        return BoardListItem(id=board_id, name=name.strip(), created_at="", updated_at=now)

    @app.get("/api/board/{board_id}", response_model=BoardData)
    async def get_specific_board(request: Request, board_id: int) -> BoardData:
        user = _get_session_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            return store.get_board_by_id(board_id, user["id"])
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.put("/api/board/{board_id}", response_model=BoardData)
    async def update_specific_board(
        request: Request, board_id: int, board: BoardData
    ) -> BoardData:
        user = _get_session_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            return store.save_board_by_id(board_id, user["id"], board)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
    return app


app = create_app()
