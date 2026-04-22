import os
import json
from typing import Any

import httpx

DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b:free"


class OpenRouterConfigError(ValueError):
    pass


def get_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise OpenRouterConfigError("OPENROUTER_API_KEY is not set.")
    return api_key


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""


async def run_openrouter_prompt(
    prompt: str,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_OPENROUTER_URL,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    return await run_openrouter_messages(
        [{"role": "user", "content": prompt}],
        api_key=api_key,
        model=model,
        endpoint=endpoint,
        transport=transport,
    )


async def run_openrouter_messages(
    messages: list[dict[str, str]],
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_OPENROUTER_URL,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=45.0, transport=transport) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        body = response.json()

    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenRouter response missing choices.")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("OpenRouter response missing message.")
    content = _extract_text_content(message.get("content"))
    if not content:
        raise ValueError("OpenRouter response content is empty.")
    return content


def extract_first_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("AI response content is empty.")

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            first = lines[0].strip().lower()
            if first == "```" or first.startswith("```json"):
                stripped = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as error:
        raise ValueError("AI response is not valid JSON.") from error

    if not isinstance(parsed, dict):
        raise ValueError("AI response JSON must be an object.")
    return parsed
