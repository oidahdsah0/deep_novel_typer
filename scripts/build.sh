#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

CONDA_ENV="${CONDA_ENV:-novel}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}}"
BUILD_API_BASE_URL_FILE="$FRONTEND_DIR/.next/novel-api-base-url.txt"
SSR_CHUNK_DIR="$FRONTEND_DIR/.next/server/chunks/ssr"
SSR_CHUNK_BACKUP_DIR="$FRONTEND_DIR/.next-novel-backup/ssr-chunks"

log() {
  printf "\033[1;34m[deep-novel-typer]\033[0m %s\n" "$*"
}

fail() {
  printf "\033[1;31m[deep-novel-typer]\033[0m %s\n" "$*" >&2
  exit 1
}

command -v conda >/dev/null 2>&1 || fail "conda is required but was not found."
command -v npm >/dev/null 2>&1 || fail "npm is required but was not found."

if ! conda run -n "$CONDA_ENV" python --version >/dev/null 2>&1; then
  log "Creating conda environment: ${CONDA_ENV}"
  conda env create -f "$BACKEND_DIR/environment.yml"
fi

if ! conda run -n "$CONDA_ENV" python -c "import fastapi, openai, uvicorn" >/dev/null 2>&1; then
  log "Installing backend dependencies into conda env: ${CONDA_ENV}"
  conda run -n "$CONDA_ENV" python -m pip install -e "$BACKEND_DIR"
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  log "Installing frontend dependencies"
  npm install --prefix "$FRONTEND_DIR"
fi

log "Cleaning stale build caches"
rm -rf "$FRONTEND_DIR/.next"

log "Building frontend for production"
(
  cd "$FRONTEND_DIR"
  export NEXT_PUBLIC_API_BASE_URL
  npm run build
)

log "Verifying frontend production build"
missing_chunks=""
while IFS= read -r map_file; do
  chunk_file="${map_file%.map}"
  if [[ ! -f "$chunk_file" ]]; then
    missing_chunks+="${chunk_file}"$'\n'
  fi
done < <(find "$SSR_CHUNK_DIR" -type f -name "*.js.map" 2>/dev/null || true)

if [[ -n "$missing_chunks" ]]; then
  printf "%s" "$missing_chunks" >&2
  fail "Production build is missing SSR chunk files. Stop any running frontend server and rerun scripts/build.sh."
fi

rm -rf "$SSR_CHUNK_BACKUP_DIR"
mkdir -p "$SSR_CHUNK_BACKUP_DIR"
while IFS= read -r chunk_file; do
  cp "$chunk_file" "$SSR_CHUNK_BACKUP_DIR/"
done < <(find "$SSR_CHUNK_DIR" -maxdepth 1 -type f -name "*.js" 2>/dev/null || true)

printf "%s\n" "$NEXT_PUBLIC_API_BASE_URL" > "$BUILD_API_BASE_URL_FILE"

log "Build complete."
