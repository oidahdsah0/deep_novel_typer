from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.APIs.dependencies import (
  api_config_service,
  database,
  file_store,
  llm_client,
  model_request_queue_service,
  project_service,
  suggestion_queue_service,
  settings,
)
from app.APIs.error_handlers import register_error_handlers
from app.APIs.routers import (
  api_configs,
  chapters,
  chat,
  debug,
  documents,
  embeddings,
  generation,
  health,
  library,
  perspectives,
  project_transfer,
  prompt_preview,
  prompt_profiles,
  projects,
  search,
  suggestions,
  typewriter_layout,
  version_settings,
  versions,
)
from app.Utils.cors import configure_cors
from app.Utils.openai_client_cache import close_cached_openai_clients


@asynccontextmanager
async def lifespan(_app: FastAPI):
  await database.initialize()
  await api_config_service.ensure_default_config()
  await project_service.bootstrap()
  await model_request_queue_service.start()
  await suggestion_queue_service.start()
  yield
  await suggestion_queue_service.shutdown()
  await api_config_service.shutdown()
  await model_request_queue_service.shutdown()
  await close_cached_openai_clients()
  await llm_client.shutdown()
  await file_store.shutdown()


app = FastAPI(
  title=settings.app_name,
  version="0.1.0",
  lifespan=lifespan,
)

configure_cors(app, settings)
register_error_handlers(app)

app.include_router(health.router)
app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
app.include_router(api_configs.router, prefix="/api/api-configs", tags=["api-configs"])
app.include_router(
  version_settings.router, prefix="/api/version-settings", tags=["version-settings"]
)
app.include_router(
  typewriter_layout.router,
  prefix="/api/typewriter-layout-settings",
  tags=["typewriter-layout"],
)
app.include_router(library.router, prefix="/api/library", tags=["library"])
app.include_router(project_transfer.router, prefix="/api/projects", tags=["project-transfer"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(embeddings.router, prefix="/api/projects/{project_id}", tags=["embeddings"])
app.include_router(search.router, prefix="/api/projects/{project_id}/search", tags=["search"])
app.include_router(chapters.router, prefix="/api/projects/{project_id}/chapters", tags=["chapters"])
app.include_router(
  documents.router, prefix="/api/projects/{project_id}/documents", tags=["documents"]
)
app.include_router(
  perspectives.router, prefix="/api/projects/{project_id}/perspectives", tags=["perspectives"]
)
app.include_router(
  prompt_profiles.router,
  prefix="/api/projects/{project_id}/prompt-profiles",
  tags=["prompt-profiles"],
)
app.include_router(
  prompt_preview.router,
  prefix="/api/projects/{project_id}/prompt-preview",
  tags=["prompt-preview"],
)
app.include_router(
  suggestions.router, prefix="/api/projects/{project_id}/suggestions", tags=["suggestions"]
)
app.include_router(chat.router, tags=["chat"])
app.include_router(
  generation.router, prefix="/api/projects/{project_id}/generation", tags=["generation"]
)
app.include_router(
  versions.router, prefix="/api/projects/{project_id}/versions", tags=["versions"]
)
