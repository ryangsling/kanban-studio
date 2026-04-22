# Project Plan - PM MVP

## Goal and approach

Build a local-first MVP project management app with:
1. Next.js frontend UI
2. FastAPI backend API plus static frontend serving
3. SQLite persistence (auto-created if missing)
4. AI chat via OpenRouter (`openai/gpt-oss-120b:free`)
5. Docker packaging and cross-platform start/stop scripts

Execution will proceed in gated phases. Part 1 is a hard gate: no implementation beyond planning until plan approval.

## Quality bar and testing policy

- Unit coverage target: **minimum 80%**, with emphasis on critical behavior (auth flow, board persistence, AI update parsing, API contracts), not metric gaming.
- Integration testing: robust API + frontend/backend flow coverage for core user journeys.
- E2E testing: at least one happy path plus selected failure-path checks for user login, board updates, and AI-assisted updates.

## Part 1 - Planning and project baseline (hard gate)

### Tasks

- [ ] Confirm requirements, technical constraints, and coding standards in root `AGENTS.md`
- [ ] Expand this plan with implementation checklists, tests, and success criteria for each phase
- [ ] Create `frontend/AGENTS.md` documenting current frontend code structure and behavior
- [ ] Pause and wait for explicit user approval before starting implementation

### Tests

- [ ] Documentation quality check: all phases include actionable tasks, tests, and completion criteria

### Success criteria

- [ ] Plan is clear enough to execute phase-by-phase without ambiguity
- [ ] Frontend baseline is documented for future migration/integration work
- [ ] User explicitly approves plan before Part 2 starts

## Part 2 - Scaffolding (Docker + FastAPI skeleton + scripts)

### Tasks

- [ ] Create backend FastAPI app scaffold in `backend/`
- [ ] Add Dockerfile and supporting configuration for single-container local run
- [ ] Use `uv` for Python dependency management in container
- [ ] Add platform start/stop scripts in `scripts/` for Linux, macOS, Windows
- [ ] Serve sample static page from FastAPI root and expose one sample API route
- [ ] Document run steps in concise root README sections

### Tests

- [ ] Backend unit tests for sample route and root handler
- [ ] Integration test: container starts and serves root HTML + API response
- [ ] Script checks: each start/stop script performs expected action

### Success criteria

- [ ] `docker` run brings up service locally without manual steps beyond documented commands
- [ ] Root (`/`) and sample API endpoint are both reachable and correct
- [ ] Start/stop scripts work on targeted platforms

## Part 3 - Frontend static build and serving from backend

### Tasks

- [ ] Configure frontend static export/build output for backend serving strategy
- [ ] Update backend static file serving to host built frontend at `/`
- [ ] Ensure existing Kanban demo renders correctly through backend
- [ ] Keep styling aligned with project color scheme and existing design

### Tests

- [ ] Frontend unit tests for board rendering behavior
- [ ] Integration test: built frontend served by FastAPI at `/`
- [ ] E2E test: load app and verify board/columns/cards baseline

### Success criteria

- [ ] Visiting `/` shows the current Kanban demo through backend
- [ ] No dependency on `next dev` at runtime in container flow
- [ ] Tests pass with meaningful coverage on board behavior

## Part 4 - Fake login flow (hardcoded credentials)

### Tasks

- [ ] Add login UI gate before board access
- [ ] Validate credentials against fixed values (`user` / `password`)
- [ ] Add logout control and session-clearing behavior
- [ ] Protect board routes/views when unauthenticated

### Tests

- [ ] Unit tests for auth form validation and state transitions
- [ ] Integration tests for auth gate and logout behavior
- [ ] E2E tests for login success/failure and post-login board visibility

### Success criteria

- [ ] Unauthenticated users cannot access board view
- [ ] Valid credentials grant access; invalid credentials show clear error
- [ ] Logout returns user to login gate and clears session state

## Part 5 - Database modeling and sign-off

### Tasks

- [ ] Define SQLite schema for users, boards, columns, cards, and ordering
- [ ] Save proposed schema as JSON in `docs/` (e.g., `docs/schema.json`)
- [ ] Add concise documentation explaining persistence model and assumptions
- [ ] Present schema for user sign-off before implementing data layer

### Tests

- [ ] Schema review checklist for required entities and relations

### Success criteria

- [ ] JSON schema is complete for MVP + future multi-user support
- [ ] Data model supports fixed-column rename, card edit, and cross-column move
- [ ] User explicitly signs off before Part 6 starts

## Part 6 - Backend API and SQLite persistence

### Tasks

- [ ] Implement SQLite initialization with create-if-missing behavior
- [ ] Add backend data-access layer for board read/write operations
- [ ] Add API endpoints for fetching and mutating signed-in user's board
- [ ] Add request/response validation models
- [ ] Ensure auth context maps changes to the correct user board

### Tests

- [ ] Backend unit tests for data access and business logic
- [ ] API integration tests for CRUD/move/reorder behaviors
- [ ] Database initialization test for missing DB startup case

### Success criteria

- [ ] API fully supports required board operations for MVP
- [ ] Persistence is stable across restarts
- [ ] Backend unit coverage reaches target with strong critical-path coverage

## Part 7 - Frontend/backend integration for persistent board

### Tasks

- [ ] Replace frontend in-memory board state with API-backed state
- [ ] Wire add/edit/move/delete/rename actions to backend endpoints
- [ ] Handle loading/error states consistently with current UX
- [ ] Keep optimistic UI simple and behavior-safe (or use immediate refresh approach)

### Tests

- [ ] Frontend unit tests for API integration logic and state updates
- [ ] Integration tests for full mutation flows against backend
- [ ] E2E tests for persistence across browser refresh/session restart

### Success criteria

- [ ] Board changes persist in SQLite and reload correctly
- [ ] Frontend and backend contracts stay consistent and typed
- [ ] Critical interaction flows are robustly tested end-to-end

## Part 8 - OpenRouter connectivity

### Tasks

- [ ] Add backend AI client wired to OpenRouter
- [ ] Read `OPENROUTER_API_KEY` from environment
- [ ] Configure model to `openai/gpt-oss-120b:free`
- [ ] Add a minimal backend AI test endpoint or diagnostic path

### Tests

- [ ] Unit test for AI client request construction
- [ ] Integration test using controlled mock for OpenRouter responses
- [ ] Manual connectivity check with prompt `2+2`

### Success criteria

- [ ] Backend can successfully call OpenRouter with configured model
- [ ] Failure modes (missing key, API error) surface clear errors
- [ ] Connectivity is proven before structured-output integration

## Part 9 - Structured AI output for chat + optional board updates

### Tasks

- [ ] Define strict structured output contract: assistant reply + optional board mutation payload
- [ ] Send current board JSON, user message, and chat history to model
- [ ] Validate AI output before applying any board updates
- [ ] Apply valid updates atomically and persist in SQLite

### Tests

- [ ] Unit tests for schema validation and mutation mapping
- [ ] Integration tests for no-op reply, valid update, and invalid payload handling
- [ ] Regression tests to ensure malformed AI output cannot corrupt board data

### Success criteria

- [ ] AI can reply conversationally and optionally update board safely
- [ ] Board update application is deterministic and validated
- [ ] Error cases are explicit and do not silently drop critical failures

## Part 10 - Frontend AI sidebar and live board refresh

### Tasks

- [ ] Build sidebar chat UI integrated with backend AI endpoint
- [ ] Show conversation history and loading/error states
- [ ] Apply AI-triggered board changes to UI automatically
- [ ] Keep UI polished and aligned with project design system/colors

### Tests

- [ ] Component tests for chat rendering and interaction states
- [ ] Integration tests for backend chat + board update roundtrip
- [ ] E2E tests covering chat-only reply and chat-with-board-update scenarios

### Success criteria

- [ ] User can chat with AI from sidebar while using board
- [ ] AI-proposed board changes are reflected immediately and persisted
- [ ] UX remains responsive, predictable, and stable
