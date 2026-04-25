import pytest

from app.Schemas.projects import CreateProjectRequest
from app.Schemas.versions import UpdateVersionSettingsRequest
from tests.service_factories import build_version_services

@pytest.mark.asyncio
async def test_version_service_saves_manual_version_and_restores_chapter(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _document_service,
    version_service,
  ) = await build_version_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "第一版正文")
    version = await version_service.create_current_version(
      project.id,
      "chapter",
      "chapter-001",
      version_type="manual",
      label="第一版",
      note="准备回溯",
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "第二版正文")

    restored = await version_service.restore_version(project.id, version.id)
    current = await chapter_service.get_chapter(project.id, "chapter-001")
    versions = await version_service.list_versions(project.id, "chapter", "chapter-001")

    assert restored.content == "第一版正文"
    assert current.content == "第一版正文"
    assert versions[0].version_type == "pre_restore"
    assert versions[-1].label == "第一版"
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_version_service_auto_version_respects_settings(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _document_service,
    version_service,
  ) = await build_version_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    settings = await version_service.update_settings(
      UpdateVersionSettingsRequest(
        auto_interval_minutes=10,
        auto_min_chars_changed=5,
        auto_min_change_ratio=0.1,
      )
    )
    assert settings.auto_min_chars_changed == 5

    chapter = await chapter_service.update_chapter(project.id, "chapter-001", "第一版正文足够长")
    first = await version_service.maybe_create_auto_version(
      project.id,
      "chapter",
      chapter.id,
      chapter.title,
      chapter.content,
    )
    updated = await chapter_service.update_chapter(project.id, "chapter-001", "第二版正文足够长")
    second = await version_service.maybe_create_auto_version(
      project.id,
      "chapter",
      updated.id,
      updated.title,
      updated.content,
    )
    versions = await version_service.list_versions(project.id, "chapter", "chapter-001")

    assert first is not None
    assert second is None
    assert len(versions) == 1
  finally:
    await store.shutdown()
