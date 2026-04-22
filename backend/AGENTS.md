# Backend overview

This folder contains the FastAPI backend scaffold for the PM MVP.

## Current scope (Part 7)

- `app/main.py`
  - Serves statically exported frontend from `frontend/out` at `/`
  - `GET /api/hello` returns `{"message":"hello world"}`
  - `GET /api/board` returns persisted board data
  - `PUT /api/board` persists board updates
  - `POST /api/ai/connectivity` calls OpenRouter with prompt `2+2`
- `app/ai.py`
  - OpenRouter request construction and response parsing
- `app/db.py`
  - SQLite schema creation and seeding
  - Board read/write logic per user
- `app/schemas.py`
  - API request/response models for board payloads
- `tests/test_main.py`
  - Unit coverage for frontend mounting and hello API response
- `tests/test_board_api.py`
  - API coverage for board fetch and persist flows
- `tests/test_ai.py`
  - OpenRouter request/response and connectivity endpoint coverage
- `tests/test_frontend_integration.py`
  - Integration coverage for serving real built frontend output
- `pyproject.toml`
  - Python dependencies managed by `uv`

## Notes

- Backend now expects frontend static build output in `frontend/out`.
- Build frontend with `npm run build` in `frontend/` before running backend tests locally.
