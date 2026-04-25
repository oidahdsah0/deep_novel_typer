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

BACKEND_PID=""
FRONTEND_PID=""

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

  wait "$FRONTEND_PID" "$BACKEND_PID" 2>/dev/null || true
}

port_is_busy() {
  lsof -iTCP:"$1" -sTCP:LISTEN -n -P >/dev/null 2>&1
}

trap cleanup EXIT INT TERM

command -v conda >/dev/null 2>&1 || fail "conda is required but was not found."
command -v npm >/dev/null 2>&1 || fail "npm is required but was not found."

if port_is_busy "$BACKEND_PORT"; then
  fail "Backend port ${BACKEND_PORT} is already in use. Set BACKEND_PORT=8001 to override."
fi

if port_is_busy "$FRONTEND_PORT"; then
  fail "Frontend port ${FRONTEND_PORT} is already in use. Set FRONTEND_PORT=3001 to override."
fi

if ! conda run -n "$CONDA_ENV" python --version >/dev/null 2>&1; then
  log "Creating conda environment: ${CONDA_ENV}"
  conda env create -f "$BACKEND_DIR/environment.yml"
fi

if ! conda run -n "$CONDA_ENV" python -c "import fastapi, openai, pytest, uvicorn" >/dev/null 2>&1; then
  log "Installing backend dependencies into conda env: ${CONDA_ENV}"
  conda run -n "$CONDA_ENV" python -m pip install -e "$BACKEND_DIR"
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  log "Installing frontend dependencies"
  npm install --prefix "$FRONTEND_DIR"
fi

log "Starting backend at http://${BACKEND_HOST}:${BACKEND_PORT}"
(
  cd "$BACKEND_DIR"
  exec conda run --no-capture-output -n "$CONDA_ENV" \
    uvicorn app.APIs.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

log "Starting frontend at http://${FRONTEND_HOST}:${FRONTEND_PORT}"
(
  cd "$FRONTEND_DIR"
  export NEXT_PUBLIC_API_BASE_URL
  exec npm run dev -- --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

log "Open http://${FRONTEND_HOST}:${FRONTEND_PORT}"
log "Press Ctrl+C to stop both services."

while true; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    fail "Backend process stopped unexpectedly."
  fi

  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    fail "Frontend process stopped unexpectedly."
  fi

  sleep 2
done
