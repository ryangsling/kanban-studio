# Scripts overview

This folder contains Docker start/stop scripts for local development.

## Scripts

- Linux
  - `start-linux.sh`
  - `stop-linux.sh`
- macOS
  - `start-mac.sh`
  - `stop-mac.sh`
- Windows (PowerShell)
  - `start-windows.ps1`
  - `stop-windows.ps1`

## Behavior

- Start scripts build image `pm-mvp`, replace any old `pm-mvp` container, and run on `http://localhost:8000`.
- Stop scripts remove the `pm-mvp` container if present.
