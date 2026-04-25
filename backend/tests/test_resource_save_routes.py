import httpx
import pytest
from fastapi import FastAPI

from app.APIs.dependencies import (
  get_chapter_service,
  get_document_service,
  get_project_service,
  get_version_service,
)
from app.APIs.error_handlers import register_error_handlers
from app.APIs.routers import chapters as chapters_router
from app.APIs.routers import documents as documents_router
from app.Schemas.projects import CreateProjectRequest
from tests.service_factories import build_version_services


@pytest.mark.asyncio
async def test_save_chapter_response_includes_project_summary_and_conflict(tmp_path) -> None:
  store, project_service, chapter_service, document_service, version_service = (
    await build_version_services(tmp_path)
  )
  app = _resource_app(project_service, chapter_service, document_service, version_service)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    base = await chapter_service.get_chapter(project.id, "chapter-001")
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
      response = await client.put(
        f"/api/projects/{project.id}/chapters/chapter-001",
        json={"content": "新的正文", "base_updated_at": base.updated_at},
      )
      stale_response = await client.put(
        f"/api/projects/{project.id}/chapters/chapter-001",
        json={"content": "旧窗口正文", "base_updated_at": base.updated_at},
      )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "新的正文"
    assert payload["project"]["id"] == project.id
    assert payload["project"]["word_count"] == payload["word_count"]
    assert stale_response.status_code == 409
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_save_chapter_writing_synopsis_response_includes_project_summary(tmp_path) -> None:
  store, project_service, chapter_service, document_service, version_service = (
    await build_version_services(tmp_path)
  )
  app = _resource_app(project_service, chapter_service, document_service, version_service)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    base = await chapter_service.get_chapter(project.id, "chapter-001")
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
      response = await client.put(
        f"/api/projects/{project.id}/chapters/chapter-001/writing-synopsis",
        json={
          "writing_synopsis": "本章写港口旧案浮出水面。",
          "base_updated_at": base.writing_synopsis_updated_at,
        },
      )
      stale_response = await client.put(
        f"/api/projects/{project.id}/chapters/chapter-001/writing-synopsis",
        json={
          "writing_synopsis": "旧窗口梗概。",
          "base_updated_at": base.writing_synopsis_updated_at,
        },
      )

    assert response.status_code == 200
    payload = response.json()
    assert payload["writing_synopsis"] == "本章写港口旧案浮出水面。"
    assert payload["project"]["id"] == project.id
    assert stale_response.status_code == 409
  finally:
    await store.shutdown()


def _resource_app(project_service, chapter_service, document_service, version_service):
  app = FastAPI()
  register_error_handlers(app)
  app.include_router(
    chapters_router.router,
    prefix="/api/projects/{project_id}/chapters",
  )
  app.include_router(
    documents_router.router,
    prefix="/api/projects/{project_id}/documents",
  )
  app.dependency_overrides[get_project_service] = lambda: project_service
  app.dependency_overrides[get_chapter_service] = lambda: chapter_service
  app.dependency_overrides[get_document_service] = lambda: document_service
  app.dependency_overrides[get_version_service] = lambda: version_service
  return app
