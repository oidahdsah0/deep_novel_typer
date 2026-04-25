import pytest

from app.Utils.errors import EntityConflictError, EntityNotFoundError
from app.Schemas.chapters import (
  CreateChapterNodeRequest,
  CreateChapterRequest,
  MoveChapterNodeRequest,
  UpdateChapterNodeRequest,
)
from app.Schemas.projects import CreateProjectRequest
from tests.service_factories import build_services

@pytest.mark.asyncio
async def test_create_chapter_appends_unique_chapter_file(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    chapter = await chapter_service.create_chapter(
      project.id, CreateChapterRequest(title="Chapter Two", content="新的线索浮出水面")
    )
    fetched = await chapter_service.get_chapter(project.id, chapter.id)

    assert chapter.id == "chapter-two"
    assert chapter.order == 2
    assert fetched.content == "新的线索浮出水面"
    assert fetched.word_count == 8
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_create_chapter_discards_temp_file_when_database_fails(tmp_path, monkeypatch) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    async def fail_upsert(*args, **kwargs):
      raise RuntimeError("index failed")

    monkeypatch.setattr(chapter_service._search_index, "upsert", fail_upsert)

    with pytest.raises(RuntimeError):
      await chapter_service.create_chapter(
        project.id, CreateChapterRequest(title="Broken Chapter", content="不会落盘")
      )

    chapter_path = tmp_path / "projects" / project.id / "chapters" / "broken-chapter.md"
    assert not chapter_path.exists()
    assert not list(chapter_path.parent.glob(".broken-chapter.md.*.tmp"))
    with pytest.raises(EntityNotFoundError):
      await chapter_service.get_chapter(project.id, "broken-chapter")
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_create_chapter_rolls_back_metadata_when_commit_fails(tmp_path, monkeypatch) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    async def fail_commit(project_id, file_path, tmp_path):
      raise OSError("replace failed")

    monkeypatch.setattr(chapter_service._content, "commit_prepared_write", fail_commit)

    with pytest.raises(OSError):
      await chapter_service.create_chapter(
        project.id, CreateChapterRequest(title="Commit Fails", content="不会落盘")
      )

    chapter_path = tmp_path / "projects" / project.id / "chapters" / "commit-fails.md"
    assert not chapter_path.exists()
    assert not list(chapter_path.parent.glob(".commit-fails.md.*.tmp"))
    with pytest.raises(EntityNotFoundError):
      await chapter_service.get_chapter(project.id, "commit-fails")
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_chapter_service_creates_tree_nodes_and_searches_content(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    folder = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="folder", title="第一卷"),
    )
    node = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(
        type="chapter",
        title="港口线索",
        parent_id=folder.id,
        content="林澈走向港口改造工地，发现旧案证词被重新装订。",
      ),
    )
    renamed = await chapter_service.update_node(
      project.id,
      node.id,
      UpdateChapterNodeRequest(title="港口线索修订"),
    )
    tree = await chapter_service.list_chapter_tree(project.id)
    phrase_results = await chapter_service.search_chapters(project.id, "港口改造")
    short_results = await chapter_service.search_chapters(project.id, "林澈")

    created_folder = next(item for item in tree if item.id == folder.id)
    assert created_folder.children[0].id == node.id
    assert created_folder.children[0].chapter_id == node.chapter_id
    assert renamed.title == "港口线索修订"
    assert phrase_results.results[0].chapter_id == node.chapter_id
    assert phrase_results.results[0].path == ["第一卷"]
    assert "港口" in phrase_results.results[0].matches[0].snippet
    assert short_results.results[0].chapter_id == node.chapter_id
    assert "林澈" in short_results.results[0].matches[-1].snippet
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_update_chapter_keeps_old_content_when_database_fails(tmp_path, monkeypatch) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "旧正文")

    async def fail_upsert(*args, **kwargs):
      raise RuntimeError("index failed")

    monkeypatch.setattr(chapter_service._search_index, "upsert", fail_upsert)

    with pytest.raises(RuntimeError):
      await chapter_service.update_chapter(project.id, "chapter-001", "新正文")

    fetched = await chapter_service.get_chapter(project.id, "chapter-001")
    assert fetched.content == "旧正文"
    assert fetched.word_count == 3
    assert not list((tmp_path / "projects" / project.id / "chapters").glob(".chapter-001.md.*.tmp"))
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_update_chapter_restores_metadata_when_commit_fails(tmp_path, monkeypatch) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    before = await chapter_service.update_chapter(project.id, "chapter-001", "旧正文")

    async def fail_commit(project_id, file_path, tmp_path):
      raise OSError("replace failed")

    monkeypatch.setattr(chapter_service._content, "commit_prepared_write", fail_commit)

    with pytest.raises(OSError):
      await chapter_service.update_chapter(project.id, "chapter-001", "新正文更多")

    fetched = await chapter_service.get_chapter(project.id, "chapter-001")
    assert fetched.content == "旧正文"
    assert fetched.word_count == before.word_count
    assert fetched.updated_at == before.updated_at
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_update_chapter_rejects_stale_base_updated_at(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    base = await chapter_service.get_chapter(project.id, "chapter-001")
    latest = await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      "新正文",
      base_updated_at=base.updated_at,
    )

    with pytest.raises(EntityConflictError, match="Chapter has changed"):
      await chapter_service.update_chapter(
        project.id,
        "chapter-001",
        "旧窗口正文",
        base_updated_at=base.updated_at,
      )

    fetched = await chapter_service.get_chapter(project.id, "chapter-001")
    assert fetched.content == "新正文"
    assert fetched.updated_at == latest.updated_at
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_update_chapter_writing_synopsis_uses_independent_lock_token(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    base = await chapter_service.get_chapter(project.id, "chapter-001")
    assert base.writing_synopsis == ""

    updated = await chapter_service.update_chapter_writing_synopsis(
      project.id,
      "chapter-001",
      "本章要让林澈意识到旧案证词被调包。",
      base_updated_at=base.writing_synopsis_updated_at,
    )

    assert updated.writing_synopsis == "本章要让林澈意识到旧案证词被调包。"
    assert updated.updated_at == base.updated_at
    assert updated.writing_synopsis_updated_at != base.writing_synopsis_updated_at

    with pytest.raises(EntityConflictError, match="synopsis has changed"):
      await chapter_service.update_chapter_writing_synopsis(
        project.id,
        "chapter-001",
        "旧窗口里的梗概。",
        base_updated_at=base.writing_synopsis_updated_at,
      )

    fetched = await chapter_service.get_chapter(project.id, "chapter-001")
    assert fetched.writing_synopsis == updated.writing_synopsis
    assert fetched.writing_synopsis_updated_at == updated.writing_synopsis_updated_at
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_chapter_service_deletes_subtree_and_search_index(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    folder = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="folder", title="第一卷"),
    )
    node = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(
        type="chapter",
        title="港口旧案",
        parent_id=folder.id,
        content="这份证词只会在删除前出现。",
      ),
    )

    await chapter_service.delete_node(project.id, folder.id)
    tree = await chapter_service.list_chapter_tree(project.id)
    search_results = await chapter_service.search_chapters(project.id, "证词")

    assert folder.id not in {item.id for item in tree}
    assert search_results.results == []
    assert not (tmp_path / "projects" / project.id / "chapters" / f"{node.chapter_id}.md").exists()
    assert list((tmp_path / "trash" / project.id / "chapter-nodes").glob(f"{folder.id}-*/manifest.json"))
    with pytest.raises(EntityNotFoundError):
      await chapter_service.get_chapter(project.id, node.chapter_id or "")
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_chapter_service_moves_nodes_and_rebuilds_reading_order(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    volume = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="folder", title="第一卷"),
    )
    later = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="chapter", title="第三章", content="第三章正文"),
    )
    moved = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="chapter", title="第二章", content="第二章正文"),
    )

    response = await chapter_service.move_node(
      project.id,
      moved.id,
      MoveChapterNodeRequest(parent_id=volume.id),
    )
    tree = response.chapter_tree
    root_ids = [node.id for node in tree]
    volume_children = next(node for node in tree if node.id == volume.id).children
    chapter_order = [chapter.id for chapter in response.chapters]

    assert root_ids == ["chapter-001", volume.id, later.id]
    assert [node.id for node in volume_children] == [moved.id]
    assert chapter_order == ["chapter-001", moved.chapter_id, later.chapter_id]

    response = await chapter_service.move_node(
      project.id,
      later.id,
      MoveChapterNodeRequest(parent_id=None, before_node_id=volume.id),
    )
    root_ids = [node.id for node in response.chapter_tree]
    chapter_order = [chapter.id for chapter in response.chapters]

    assert root_ids == ["chapter-001", later.id, volume.id]
    assert chapter_order == ["chapter-001", later.chapter_id, moved.chapter_id]
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_chapter_service_rejects_moving_folder_into_descendant(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    parent = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="folder", title="父目录"),
    )
    child = await chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="folder", title="子目录", parent_id=parent.id),
    )

    with pytest.raises(EntityConflictError):
      await chapter_service.move_node(
        project.id,
        parent.id,
        MoveChapterNodeRequest(parent_id=child.id),
      )
  finally:
    await store.shutdown()
