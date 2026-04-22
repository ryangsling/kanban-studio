# Backend overview

This folder contains the FastAPI backend scaffold for the PM MVP.

## Current scope (Part 4)

- `app/main.py`
  - Serves statically exported frontend from `frontend/out` at `/`
  - Frontend now includes login gate (`user` / `password`) and logout flow
  - `GET /api/hello` returns `{"message":"hello world"}`
- `tests/test_main.py`
  - Unit coverage for frontend mounting and hello API response
- `tests/test_frontend_integration.py`
  - Integration coverage for serving real built frontend output
- `pyproject.toml`
  - Python dependencies managed by `uv`

## Notes

- Backend now expects frontend static build output in `frontend/out`.
- Build frontend with `npm run build` in `frontend/` before running backend tests locally.
