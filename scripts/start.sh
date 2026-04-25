#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

CONDA_ENV="${CONDA_ENV:-novel}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}}"
BUILD_API_BASE_URL_FILE="$FRONTEND_DIR/.next/novel-api-base-url.txt"
SSR_CHUNK_DIR="$FRONTEND_DIR/.next/server/chunks/ssr"
SSR_CHUNK_BACKUP_DIR="$FRONTEND_DIR/.next-novel-backup/ssr-chunks"
APP_ROUTE_DIR="$FRONTEND_DIR/.next/server/app"
APP_ROUTE_BACKUP_DIR="$FRONTEND_DIR/.next-novel-backup/server-app"

BACKEND_PID=""
FRONTEND_PID=""
RESTORE_PID=""

log() {
  printf "\033[1;34m[deep-novel-typer]\033[0m %s\n" "$*"
}

fail() {
  printf "\033[1;31m[deep-novel-typer]\033[0m %s\n" "$*" >&2
  exit 1
}

cleanup() {
  trap - EXIT INT TERM

  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$RESTORE_PID" ]] && kill -0 "$RESTORE_PID" 2>/dev/null; then
    kill "$RESTORE_PID" 2>/dev/null || true
  fi

  wait "$FRONTEND_PID" "$BACKEND_PID" "$RESTORE_PID" 2>/dev/null || true
}

restore_turbopack_chunks() {
  local quiet="${1:-0}"

  if [[ ! -d "$SSR_CHUNK_DIR" ]] || [[ ! -d "$SSR_CHUNK_BACKUP_DIR" ]]; then
    return 0
  fi

  local restored=0
  local backup_file
  local chunk_file

  while IFS= read -r backup_file; do
    chunk_file="$SSR_CHUNK_DIR/$(basename "$backup_file")"
    if [[ ! -f "$chunk_file" ]]; then
      cp "$backup_file" "$chunk_file"
      restored=$((restored + 1))
    fi
  done < <(find "$SSR_CHUNK_BACKUP_DIR" -maxdepth 1 -type f -name "*.js" 2>/dev/null || true)

  if (( restored > 0 )) && [[ "$quiet" != "1" ]]; then
    log "Restored ${restored} production SSR chunk(s)"
  fi
}

restore_app_route_files() {
  local quiet="${1:-0}"

  if [[ ! -d "$APP_ROUTE_BACKUP_DIR" ]]; then
    return 0
  fi

  local restored=0
  local backup_file
  local relative_path
  local route_file

  while IFS= read -r backup_file; do
    relative_path="${backup_file#"$APP_ROUTE_BACKUP_DIR"/}"
    route_file="$APP_ROUTE_DIR/$relative_path"
    if [[ ! -f "$route_file" ]]; then
      mkdir -p "$(dirname "$route_file")"
      cp "$backup_file" "$route_file"
      restored=$((restored + 1))
    fi
  done < <(find "$APP_ROUTE_BACKUP_DIR" -type f 2>/dev/null || true)

  if (( restored > 0 )) && [[ "$quiet" != "1" ]]; then
    log "Restored ${restored} production app route file(s)"
  fi
}

restore_production_files() {
  local quiet="${1:-0}"
  restore_turbopack_chunks "$quiet"
  restore_app_route_files "$quiet"
}

start_restore_guard() {
  (
    while true; do
      restore_production_files 1
      sleep 0.2
    done
  ) &
  RESTORE_PID=$!
}

port_is_busy() {
  lsof -iTCP:"$1" -sTCP:LISTEN -n -P >/dev/null 2>&1
}

trap cleanup EXIT INT TERM

command -v conda >/dev/null 2>&1 || fail "conda is required but was not found."

if ! conda run -n "$CONDA_ENV" python --version >/dev/null 2>&1; then
  fail "Conda env ${CONDA_ENV} not found. Run scripts/build.sh first."
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  fail "Frontend node_modules not found. Run scripts/build.sh first."
fi

if [[ ! -d "$FRONTEND_DIR/.next" ]]; then
  fail "Frontend production build not found. Run scripts/build.sh first."
fi

if [[ -f "$BUILD_API_BASE_URL_FILE" ]]; then
  BUILD_API_BASE_URL="$(<"$BUILD_API_BASE_URL_FILE")"
  if [[ "$BUILD_API_BASE_URL" != "$NEXT_PUBLIC_API_BASE_URL" ]]; then
    fail "Frontend build uses ${BUILD_API_BASE_URL}, but start requested ${NEXT_PUBLIC_API_BASE_URL}. Rerun scripts/build.sh with the same BACKEND_HOST/BACKEND_PORT or NEXT_PUBLIC_API_BASE_URL."
  fi
else
  fail "Frontend build API marker not found. Rerun scripts/build.sh before scripts/start.sh."
fi

restore_production_files
start_restore_guard

if port_is_busy "$BACKEND_PORT"; then
  fail "Backend port ${BACKEND_PORT} is already in use. Set BACKEND_PORT=8001 to override."
fi

if port_is_busy "$FRONTEND_PORT"; then
  fail "Frontend port ${FRONTEND_PORT} is already in use. Set FRONTEND_PORT=3001 to override."
fi

log "Starting backend at http://${BACKEND_HOST}:${BACKEND_PORT}"
(
  cd "$BACKEND_DIR"
  exec conda run --no-capture-output -n "$CONDA_ENV" \
    uvicorn app.APIs.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

log "Starting production frontend at http://${FRONTEND_HOST}:${FRONTEND_PORT}"
(
  cd "$FRONTEND_DIR"
  export NEXT_PUBLIC_API_BASE_URL
  exec npm run start -- --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

sleep 1
restore_production_files

log "Open http://${FRONTEND_HOST}:${FRONTEND_PORT}"
log "Press Ctrl+C to stop both services."

while true; do
  restore_production_files

  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    fail "Backend process stopped unexpectedly."
  fi

  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    fail "Frontend process stopped unexpectedly."
  fi

  sleep 2
done
