import pytest

from app.Utils.db import AsyncDatabase
from app.Schemas.projects import CreateProjectRequest, UpdateProjectRequest
from tests.service_factories import build_services


@pytest.mark.asyncio
async def test_bootstrap_does_not_seed_demo_project(tmp_path) -> None:
  store, project_service, _chapter_service, _document_service = await build_services(tmp_path)
  try:
    await project_service.bootstrap()

    assert await project_service.list_projects() == []
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_created_project_starts_with_empty_first_chapter(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    chapter = await chapter_service.get_chapter(project.id, "chapter-001")

    assert chapter.content == ""
    assert chapter.word_count == 0
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_created_project_starts_with_single_basic_blueprint(tmp_path) -> None:
  store, project_service, _chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    assert [(document.kind, document.title) for document in project.documents] == [
      ("outline", "基本蓝图"),
    ]
    docs_dir = tmp_path / "projects" / project.id / "docs"
    assert (docs_dir / "outline.md").read_text() == (
      "# 基本蓝图\n\n"
      "## 核心概念\n\n"
      "## 主线方向\n\n"
      "## 角色与关系\n\n"
      "## 世界设定\n\n"
      "## 待补充\n"
    )
    assert not (docs_dir / "design.md").exists()
    assert not (docs_dir / "notes.md").exists()
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_database_migration_removes_legacy_default_perspectives_once(tmp_path) -> None:
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  documents_table = await db.fetch_one(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'documents'"
  )
  assert documents_table is None
  now = "2026-04-27T00:00:00+00:00"
  await db.execute(
    """
    INSERT INTO projects (
      id, title, subtitle, description, genre, status, root_path,
      created_at, updated_at, last_opened_at, deleted_at
    )
    VALUES ('book-1', 'Book', '', '', '', 'drafting', 'book-1', ?, ?, NULL, NULL)
    """,
    (now, now),
  )
  for perspective_id in ("pace-editor", "character-critic", "continuity", "custom-view"):
    await db.execute(
      """
      INSERT INTO perspectives (
        id, project_id, name, description, instructions, is_enabled, created_at, updated_at
      )
      VALUES (?, 'book-1', ?, '', 'instructions', 1, ?, ?)
      """,
      (perspective_id, perspective_id, now, now),
    )
  await db.execute(
    "DELETE FROM schema_migrations WHERE id = 'remove-legacy-default-perspectives-v1'"
  )

  await db.initialize()

  rows = await db.fetch_all("SELECT id FROM perspectives ORDER BY id")
  assert [row["id"] for row in rows] == ["custom-view"]

  await db.execute(
    """
    INSERT INTO perspectives (
      id, project_id, name, description, instructions, is_enabled, created_at, updated_at
    )
    VALUES ('pace-editor', 'book-1', 'Pace Editor', '', 'manual instructions', 1, ?, ?)
    """,
    (now, now),
  )
  await db.initialize()

  rows = await db.fetch_all("SELECT id FROM perspectives ORDER BY id")
  assert [row["id"] for row in rows] == ["custom-view", "pace-editor"]


@pytest.mark.asyncio
async def test_project_update_and_soft_delete_round_trip(tmp_path) -> None:
  store, project_service, _chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    updated = await project_service.update_project(
      project.id,
      UpdateProjectRequest(description="新的设定", genre="悬疑", status="revising"),
    )

    deleted = await project_service.trash_project(project.id)
    active_projects = await project_service.list_projects()
    restored = await project_service.restore_project(project.id)

    assert updated.description == "新的设定"
    assert updated.genre == "悬疑"
    assert updated.status == "revising"
    assert deleted.deleted_at is not None
    assert active_projects == []
    assert restored.deleted_at is None
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_trash_project_rolls_back_database_when_move_fails(tmp_path, monkeypatch) -> None:
  store, project_service, _chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    source = tmp_path / "projects" / project.id

    async def fail_move_dir(source_path, target_path):
      raise OSError("move failed")

    monkeypatch.setattr(store, "move_dir", fail_move_dir)

    with pytest.raises(OSError):
      await project_service.trash_project(project.id)

    restored = await project_service.get_manifest(project.id)
    row = await project_service._repository.get_project_row(project.id)
    assert restored.deleted_at is None
    assert row["deleted_at"] is None
    assert row["root_path"] == str(source)
    assert source.exists()
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_restore_project_rolls_back_database_when_move_fails(tmp_path, monkeypatch) -> None:
  store, project_service, _chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    deleted = await project_service.trash_project(project.id)
    row_before = await project_service._repository.get_project_row(
      project.id, include_deleted=True
    )

    async def fail_move_dir(source_path, target_path):
      raise OSError("move failed")

    monkeypatch.setattr(store, "move_dir", fail_move_dir)

    with pytest.raises(OSError):
      await project_service.restore_project(project.id)

    row_after = await project_service._repository.get_project_row(
      project.id, include_deleted=True
    )
    assert row_after["deleted_at"] == deleted.deleted_at
    assert row_after["root_path"] == row_before["root_path"]
    assert await project_service.list_projects() == []
  finally:
    await store.shutdown()
