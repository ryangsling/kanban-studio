#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="pm-mvp"
CONTAINER_NAME="pm-mvp"
VOLUME_NAME="pm-mvp-data"

docker build --tag "$IMAGE_NAME" "$ROOT_DIR"

if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

docker volume create "$VOLUME_NAME" >/dev/null

docker run \
  --detach \
  --name "$CONTAINER_NAME" \
  --publish 8000:8000 \
  --volume "$VOLUME_NAME:/data" \
  --env DB_PATH=/data/pm.db \
  "$IMAGE_NAME" >/dev/null

echo "PM MVP started: http://localhost:8000"
