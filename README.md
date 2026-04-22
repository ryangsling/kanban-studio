# PM MVP

Local Dockerized scaffold for the Project Management MVP.

## Part 8 status

- FastAPI serves statically exported frontend at `/`
- Login gate at `/` using fixed credentials (`user` / `password`)
- Kanban board is persisted in SQLite
- Board API:
  - `GET /api/board?username=user`
  - `PUT /api/board?username=user`
- API hello endpoint at `/api/hello`
- OpenRouter connectivity endpoint: `POST /api/ai/connectivity` (sends prompt `2+2`)
- Dockerized runtime
- Cross-platform start/stop scripts in `scripts/`

## Run

Linux:

```bash
./scripts/start-linux.sh
./scripts/stop-linux.sh
```

macOS:

```bash
./scripts/start-mac.sh
./scripts/stop-mac.sh
```

Windows (PowerShell):

```powershell
./scripts/start-windows.ps1
./scripts/stop-windows.ps1
```

Then open `http://localhost:8000`, sign in with `user` / `password`, and call:
- `http://localhost:8000/api/hello`
- `http://localhost:8000/api/board?username=user`
- `http://localhost:8000/api/ai/connectivity` (POST)

The start scripts now mount a named Docker volume (`pm-mvp-data`) and store SQLite at `/data/pm.db`, so board data persists across container stop/start.

Set `OPENROUTER_API_KEY` in root `.env` before calling AI connectivity.
The start scripts pass `.env` to the container automatically when that file exists.
