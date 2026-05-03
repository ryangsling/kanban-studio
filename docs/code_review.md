# Comprehensive Code Review — Kanban Studio

Date: 2026-04-23
Scope: backend, frontend, tests, container/deploy config, scripts

## Executive summary

Repo is clean, readable, and mostly consistent with MVP goals. Core behavior covered by tests and critical paths pass locally:
- Backend tests: 12/12 pass
- Frontend unit tests: 10/10 pass
- Frontend lint: 1 warning
- E2E: execution started but did not complete within review window

Biggest risks now are security model (no real auth boundary on API), state consistency under concurrent UI saves, and CI/test hardening.

## What is strong

1. **Clear domain contracts and validation**
   - Pydantic models enforce board/chat shapes (`backend/app/schemas.py:6`).
   - AI response is parsed + schema-validated before persistence (`backend/app/main.py:144`).

2. **Defensive board integrity checks**
   - Duplicate columns/cards and mismatched card maps are rejected (`backend/app/db.py:233`).
   - Column reorder handled safely around unique-position constraints (`backend/app/db.py:263`).

3. **Good baseline tests on core flows**
   - API + AI integration tests cover noop, valid update, invalid update (`backend/tests/test_ai.py:101`, `backend/tests/test_ai.py:141`, `backend/tests/test_ai.py:180`).
   - UI tests cover login, board actions, AI sidebar responses (`frontend/src/components/AppShell.test.tsx:20`).

## Findings and actions

### P0 (fix soon)

#### 1) API has no server-side auth; `username` query param controls data access
- Evidence:
  - Board endpoints trust query param directly (`backend/app/main.py:99`, `backend/app/main.py:107`).
  - Frontend login is localStorage-only gate (`frontend/src/components/AppShell.tsx:22`, `frontend/src/components/AppShell.tsx:79`).
- Risk:
  - Any caller can hit `/api/board?username=user` and read/write board without session proof.
- Action:
  1. Remove client-controlled `username` from API contract.
  2. Add backend auth/session boundary (even minimal cookie session for MVP).
  3. Derive user identity from authenticated session, not query string.

#### 2) Plain SHA-256 for password storage (no salt/work factor)
- Evidence: `_hash_password` uses raw SHA-256 (`backend/app/db.py:15`).
- Risk:
  - Fast offline cracking if DB leaks.
- Action:
  1. Replace with Argon2id/bcrypt (`pwdlib`/`passlib`).
  2. Store hash format metadata; migrate seeded user on startup.

### P1 (next sprint)

#### 3) Potential stale-write race in frontend persistence path
- Evidence:
  - `handleBoardChange` saves each change async and sets state from response (`frontend/src/components/AppShell.tsx:101`).
- Risk:
  - Rapid edits can resolve out of order; older response may overwrite newer local state.
- Action:
  1. Add request sequencing/version token; ignore stale responses.
  2. Or serialize saves with queue/debounce and last-write-wins guard.

#### 4) AI endpoint lacks explicit input size limits and rate guards
- Evidence:
  - `/api/ai/chat` accepts board + history; only windowing done in message construction (`backend/app/main.py:45`, `backend/app/main.py:134`).
- Risk:
  - Large payload cost spikes, slow requests, and accidental abuse.
- Action:
  1. Add max request body size and max message length.
  2. Add per-IP/user rate limiting at app/proxy layer.
  3. Return structured 429/413 errors.

#### 5) Test pipeline reliability gap: E2E command heavyweight and flaky risk
- Evidence:
  - Playwright webServer command performs build + uv sync + server startup inline (`frontend/playwright.config.ts:15`).
- Risk:
  - Slow/fragile CI startup, harder debugging.
- Action:
  1. Pre-build dependencies in CI steps.
  2. Keep Playwright `webServer.command` to app startup only.
  3. Add explicit CI timeout and retry policy for flaky browser tests.

### P2 (cleanup / quality)

#### 6) Lint warning in test code
- Evidence: unused `init` var (`frontend/src/components/AppShell.test.tsx:81`).
- Action:
  - Remove unused parameter or use `_init` and eslint ignore pattern.

#### 7) Stale/unused static artifact in backend tree
- Evidence:
  - `backend/app/static/index.html` exists (`backend/app/static/index.html:1`) but app serves `frontend/out` (`backend/app/main.py:27`, `backend/app/main.py:169`).
- Action:
  - Delete stale file or document fallback use to prevent confusion.

#### 8) Plan doc status drift vs implementation state
- Evidence:
  - `docs/PLAN.md` says Parts 9/10 pending (`docs/PLAN.md:23`) but AI structured output + sidebar already implemented (`backend/app/main.py:134`, `frontend/src/components/AiSidebar.tsx:16`).
- Action:
  - Update plan status to match current reality.

## Suggested implementation order

1. Server-side auth boundary + remove `username` query identity.
2. Password hashing upgrade (Argon2id/bcrypt).
3. Frontend save-order race fix.
4. AI endpoint size/rate limits.
5. CI/E2E split and hardening.
6. Repo hygiene cleanups (lint warning, stale static file, docs sync).

## Optional hardening after above

- Add optimistic-lock field (`board_version`) to prevent lost updates server-side.
- Add request/response audit logging for AI mutation operations (with redaction).
- Add coverage threshold enforcement in test config/CI.
