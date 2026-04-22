import json
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from fastapi.testclient import TestClient

from app.ai import DEFAULT_MODEL, run_openrouter_prompt
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
