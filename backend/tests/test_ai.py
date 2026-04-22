import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from fastapi.testclient import TestClient

from app.ai import DEFAULT_MODEL, extract_first_json_object, run_openrouter_prompt
from app.main import create_app


def test_openrouter_request_construction_and_parse() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("Authorization")
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "4",
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    response = asyncio.run(
        run_openrouter_prompt(
            "2+2",
            api_key="test-key",
            model=DEFAULT_MODEL,
            endpoint="https://openrouter.example/api/v1/chat/completions",
            transport=transport,
        )
    )

    assert response == "4"
    assert captured["url"] == "https://openrouter.example/api/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["body"] == {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": "2+2"}],
        "temperature": 0,
    }


def test_connectivity_endpoint_uses_openrouter_response(monkeypatch) -> None:
    async def fake_run_openrouter_prompt(prompt: str, *, api_key: str, **_kwargs) -> str:
        assert prompt == "2+2"
        assert api_key == "fake-key"
        return "4"

    monkeypatch.setattr("app.main.get_openrouter_api_key", lambda: "fake-key")
    monkeypatch.setattr("app.main.run_openrouter_prompt", fake_run_openrouter_prompt)

    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir)
        db_path = dist / "test.db"
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))
        response = client.post("/api/ai/connectivity")

    assert response.status_code == 200
    assert response.json() == {"model": DEFAULT_MODEL, "prompt": "2+2", "response": "4"}


def test_connectivity_endpoint_requires_api_key(monkeypatch) -> None:
    from app.ai import OpenRouterConfigError

    def missing_key() -> str:
        raise OpenRouterConfigError("OPENROUTER_API_KEY is not set.")

    monkeypatch.setattr("app.main.get_openrouter_api_key", missing_key)

    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir)
        db_path = dist / "test.db"
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))
        response = client.post("/api/ai/connectivity")

    assert response.status_code == 500
    assert response.json() == {"detail": "OPENROUTER_API_KEY is not set."}


def test_extract_first_json_object_rejects_non_json() -> None:
    try:
        extract_first_json_object("not-json")
        assert False, "Expected ValueError for invalid JSON."
    except ValueError as error:
        assert str(error) == "AI response is not valid JSON."


def test_ai_chat_noop_response(monkeypatch) -> None:
    async def fake_run_openrouter_messages(messages, *, api_key: str, **_kwargs) -> str:
        assert api_key == "fake-key"
        assert messages[-1]["role"] == "user"
        return json.dumps(
            {
                "assistantMessage": "No board update needed.",
                "boardUpdate": None,
            }
        )

    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))
        board = client.get("/api/board").json()

        monkeypatch.setattr("app.main.get_openrouter_api_key", lambda: "fake-key")
        monkeypatch.setattr("app.main.run_openrouter_messages", fake_run_openrouter_messages)

        response = client.post(
            "/api/ai/chat",
            json={
                "message": "What should I do next?",
                "board": board,
                "history": [{"role": "user", "content": "Earlier question"}],
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "model": DEFAULT_MODEL,
        "assistantMessage": "No board update needed.",
        "boardUpdated": False,
        "board": None,
    }


def test_ai_chat_applies_valid_board_update(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))
        board = client.get("/api/board").json()

        reordered_columns = [board["columns"][1], board["columns"][0], *board["columns"][2:]]
        reordered_columns[0]["title"] = "Discovery Queue"
        updated_board = {"columns": reordered_columns, "cards": board["cards"]}

        async def fake_run_openrouter_messages(_messages, *, api_key: str, **_kwargs) -> str:
            assert api_key == "fake-key"
            return json.dumps(
                {
                    "assistantMessage": "I reordered columns and renamed one.",
                    "boardUpdate": updated_board,
                }
            )

        monkeypatch.setattr("app.main.get_openrouter_api_key", lambda: "fake-key")
        monkeypatch.setattr("app.main.run_openrouter_messages", fake_run_openrouter_messages)

        response = client.post(
            "/api/ai/chat",
            json={"message": "Reorder columns.", "board": board, "history": []},
        )
        persisted = client.get("/api/board").json()

    assert response.status_code == 200
    assert response.json()["boardUpdated"] is True
    assert response.json()["board"]["columns"][0]["id"] == "col-discovery"
    assert response.json()["board"]["columns"][0]["title"] == "Discovery Queue"
    assert persisted["columns"][0]["id"] == "col-discovery"
    assert persisted["columns"][0]["title"] == "Discovery Queue"


def test_ai_chat_rejects_invalid_board_update_and_keeps_board_unchanged(
    monkeypatch,
) -> None:
    with TemporaryDirectory() as temp_dir:
        dist = Path(temp_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        db_path = Path(temp_dir) / "test.db"
        client = TestClient(create_app(frontend_dist=dist, db_path=db_path))
        board = client.get("/api/board").json()
        invalid_board = dict(board)
        invalid_board["columns"] = [*board["columns"]]
        invalid_board["columns"][0] = dict(invalid_board["columns"][0])
        invalid_board["columns"][0]["cardIds"] = [*invalid_board["columns"][0]["cardIds"], "ghost-card"]

        async def fake_run_openrouter_messages(_messages, *, api_key: str, **_kwargs) -> str:
            assert api_key == "fake-key"
            return json.dumps(
                {
                    "assistantMessage": "Done.",
                    "boardUpdate": invalid_board,
                }
            )

        monkeypatch.setattr("app.main.get_openrouter_api_key", lambda: "fake-key")
        monkeypatch.setattr("app.main.run_openrouter_messages", fake_run_openrouter_messages)

        response = client.post(
            "/api/ai/chat",
            json={"message": "Break it", "board": board, "history": []},
        )
        after = client.get("/api/board").json()

    assert response.status_code == 502
    assert "AI response is invalid" in response.json()["detail"]
    assert after == board
