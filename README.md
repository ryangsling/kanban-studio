# PM MVP

Local Dockerized scaffold for the Project Management MVP.

## Part 4 status

- FastAPI backend scaffold in `backend/`
- Frontend statically exported from `frontend/` and served by FastAPI at `/`
- Login gate at `/` using fixed credentials (`user` / `password`)
- Logout control that returns to the login screen
- API hello endpoint at `/api/hello`
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

Then open `http://localhost:8000`, sign in with `user` / `password`, and call `http://localhost:8000/api/hello`.
