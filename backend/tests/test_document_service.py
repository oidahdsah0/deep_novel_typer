from contextlib import asynccontextmanager

import pytest

from app.Utils.errors import EntityConflictError, EntityNotFoundError
from app.Schemas.documents import (
  CreateDocumentNodeRequest,
  MoveDocumentNodeRequest,
  UpdateDocumentNodeRequest,
)
from app.Schemas.projects import CreateProjectRequest
from tests.service_factories import build_services

def _patch_transaction_to_fail(db, monkeypatch) -> None:
  real_transaction = db.transaction

  @asynccontextmanager
  async def failing_transaction():
    async with real_transaction() as conn:

      async def execute(query, params=()):
        raise RuntimeError("database unavailable")

      conn.execute = execute
      yield conn

  monkeypatch.setattr(db, "transaction", failing_transaction)


@pytest.mark.asyncio
async def test_document_service_reads_and_updates_project_documents(tmp_path) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    outline = await document_service.get_document(project.id, "outline")
    updated = await document_service.update_document(project.id, "outline", "# 新大纲\n")
    renamed = await document_service.update_node(
      project.id,
      "outline",
      UpdateDocumentNodeRequest(title="重命名大纲"),
    )
    documents = await document_service.list_documents(project.id)

    assert outline.title == "基本蓝图"
    assert updated.content == "# 新大纲\n"
    assert updated.updated_at != outline.updated_at
    assert renamed.title == "重命名大纲"
    assert next(document for document in documents if document.kind == "outline").title == "重命名大纲"
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_document_service_deletes_subtree_and_moves_files_to_trash(tmp_path) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    folder = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(type="folder", title="资料夹"),
    )
    document = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(
        type="markdown",
        title="可删除资料",
        parent_id=folder.id,
        content="## 临时资料\n",
      ),
    )

    await document_service.delete_node(project.id, folder.id)
    tree = await document_service.list_document_tree(project.id)

    assert folder.id not in {item.id for item in tree}
    assert not (tmp_path / "projects" / project.id / "docs" / f"{document.id}.md").exists()
    assert list((tmp_path / "trash" / project.id / "document-nodes").glob(f"{folder.id}-*/manifest.json"))
    with pytest.raises(EntityNotFoundError):
      await document_service.get_document(project.id, document.id)
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_document_service_creates_folder_and_markdown_nodes(tmp_path) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    folder = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(type="folder", title="世界观"),
    )
    document = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(
        type="markdown",
        title="港口传说",
        parent_id=folder.id,
        content="## 传说\n\n潮水会带回旧案。",
      ),
    )
    renamed = await document_service.update_node(
      project.id,
      document.id,
      UpdateDocumentNodeRequest(title="港口传说索引"),
    )
    detail = await document_service.get_document(project.id, document.id)
    updated = await document_service.update_document(project.id, document.id, "## 传说\n\n新的线索。")
    tree = await document_service.list_document_tree(project.id)

    assert folder.type == "folder"
    assert document.parent_id == folder.id
    assert renamed.title == "港口传说索引"
    assert detail.content == "## 传说\n\n潮水会带回旧案。"
    assert updated.content == "## 传说\n\n新的线索。"
    created_folder = next(node for node in tree if node.id == folder.id)
    assert [child.id for child in created_folder.children] == [document.id]
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_document_create_rolls_back_metadata_when_commit_fails(tmp_path, monkeypatch) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    async def fail_commit(tmp_path_arg, target_path):
      raise OSError("replace failed")

    monkeypatch.setattr(store, "commit_text_temp", fail_commit)

    with pytest.raises(OSError):
      await document_service.create_node(
        project.id,
        CreateDocumentNodeRequest(
          type="markdown",
          title="Fail Doc",
          content="不会落盘",
        ),
      )

    document_path = tmp_path / "projects" / project.id / "docs" / "fail-doc.md"
    assert not document_path.exists()
    assert not list(document_path.parent.glob(".fail-doc.md.*.tmp"))
    with pytest.raises(EntityNotFoundError):
      await document_service.get_document(project.id, "fail-doc")
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_document_update_restores_metadata_when_commit_fails(tmp_path, monkeypatch) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    before = await document_service.update_document(project.id, "outline", "# 旧大纲\n")

    async def fail_commit(tmp_path_arg, target_path):
      raise OSError("replace failed")

    monkeypatch.setattr(store, "commit_text_temp", fail_commit)

    with pytest.raises(OSError):
      await document_service.update_document(project.id, "outline", "# 新大纲\n")

    fetched = await document_service.get_document(project.id, "outline")
    assert fetched.content == "# 旧大纲\n"
    assert fetched.updated_at == before.updated_at
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_document_create_discards_temp_when_database_fails(tmp_path, monkeypatch) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    _patch_transaction_to_fail(document_service._db, monkeypatch)

    with pytest.raises(RuntimeError, match="database unavailable"):
      await document_service.create_node(
        project.id,
        CreateDocumentNodeRequest(type="markdown", title="Db Fail Doc", content="不会落盘"),
      )

    document_path = tmp_path / "projects" / project.id / "docs" / "db-fail-doc.md"
    assert not document_path.exists()
    assert not list(document_path.parent.glob(".db-fail-doc.md.*.tmp"))
    with pytest.raises(EntityNotFoundError):
      await document_service.get_document(project.id, "db-fail-doc")
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_document_update_keeps_old_content_when_database_fails(tmp_path, monkeypatch) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    before = await document_service.update_document(project.id, "outline", "# 旧大纲\n")
    _patch_transaction_to_fail(document_service._db, monkeypatch)

    with pytest.raises(RuntimeError, match="database unavailable"):
      await document_service.update_document(project.id, "outline", "# 新大纲\n")

    fetched = await document_service.get_document(project.id, "outline")
    assert fetched.content == "# 旧大纲\n"
    assert fetched.updated_at == before.updated_at
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_update_document_rejects_stale_base_updated_at(tmp_path) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    base = await document_service.get_document(project.id, "outline")
    latest = await document_service.update_document(
      project.id,
      "outline",
      "# 新大纲\n",
      base_updated_at=base.updated_at,
    )

    with pytest.raises(EntityConflictError, match="Document has changed"):
      await document_service.update_document(
        project.id,
        "outline",
        "# 旧窗口大纲\n",
        base_updated_at=base.updated_at,
      )

    fetched = await document_service.get_document(project.id, "outline")
    assert fetched.content == "# 新大纲\n"
    assert fetched.updated_at == latest.updated_at
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_document_service_moves_nodes_between_folders(tmp_path) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    folder = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(type="folder", title="资料夹"),
    )
    second = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(type="markdown", title="第二份资料", content="第二份"),
    )
    moved = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(type="markdown", title="第一份资料", content="第一份"),
    )

    response = await document_service.move_node(
      project.id,
      moved.id,
      MoveDocumentNodeRequest(parent_id=folder.id),
    )
    root_ids = [node.id for node in response.document_tree]
    folder_children = next(node for node in response.document_tree if node.id == folder.id).children

    assert root_ids == ["outline", folder.id, second.id]
    assert [node.id for node in folder_children] == [moved.id]

    response = await document_service.move_node(
      project.id,
      second.id,
      MoveDocumentNodeRequest(parent_id=None, before_node_id=folder.id),
    )
    root_ids = [node.id for node in response.document_tree]
    assert root_ids == ["outline", second.id, folder.id]
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_document_service_rejects_moving_folder_into_descendant(tmp_path) -> None:
  store, project_service, _chapter_service, document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    parent = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(type="folder", title="父目录"),
    )
    child = await document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(type="folder", title="子目录", parent_id=parent.id),
    )

    with pytest.raises(EntityConflictError):
      await document_service.move_node(
        project.id,
        parent.id,
        MoveDocumentNodeRequest(parent_id=child.id),
      )
  finally:
    await store.shutdown()
