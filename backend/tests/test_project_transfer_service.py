from __future__ import annotations

import json
import zipfile
from io import BytesIO

import pytest

from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.perspective_service import PerspectiveService
from app.Services.prompt_profiles import PromptProfileService
from app.Services.project_service import ProjectService
from app.Services.project_transfer import ProjectTransferService
from app.Services.project_transfer.import_cleanup import cleanup_import_target
from app.Services.version_service import VersionService
from app.Utils.config import _load_llm_settings
from app.Utils.db import AsyncDatabase
from app.Utils.errors import DomainError, InvalidProjectPathError
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.chapters import CreateChapterNodeRequest
from app.Schemas.documents import CreateDocumentNodeRequest
from app.Schemas.perspectives import CreatePerspectiveRequest, UpdatePerspectiveRequest
from app.Schemas.projects import CreateProjectRequest
from app.Schemas.prompt_profiles import UpdatePromptProfileRequest


@pytest.mark.asyncio
async def test_project_transfer_exports_and_imports_full_project(tmp_path) -> None:
  source = await _build_transfer_stack(tmp_path / "source")
  target = await _build_transfer_stack(tmp_path / "target")
  try:
    project = await source.project_service.create_project(
      CreateProjectRequest(title="Transfer Book", genre="悬疑")
    )
    await source.chapter_service.update_chapter(
      project.id,
      "chapter-001",
      "第一章正文。\n\n雾从码头升起。",
    )
    folder = await source.chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="folder", title="第二卷"),
    )
    chapter = await source.chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(
        type="chapter",
        title="第二章 回声",
        parent_id=folder.id,
        content="第二章正文。",
      ),
    )
    doc_folder = await source.document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(type="folder", title="资料夹"),
    )
    doc = await source.document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(
        type="markdown",
        title="港口档案",
        parent_id=doc_folder.id,
        content="# 港口档案\n\n- 旧码头。",
      ),
    )
    api_config = await source.api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Export Only Config",
        api_key="source-secret",
        base_url="https://export-only.example.test",
        model="export-only-model",
        thinking_enabled=False,
      )
    )
    await source.perspective_service.create_perspective(
      project.id,
      CreatePerspectiveRequest(
        name="Pace Editor",
        description="关注节奏。",
        instructions="检查节奏。",
      ),
    )
    await source.perspective_service.update_perspective(
      project.id,
      "pace-editor",
      UpdatePerspectiveRequest(api_config_id=api_config.id),
    )
    await source.db.execute(
      """
      INSERT INTO generation_presets (
        project_id, kind, preset_id, name, content, is_system, is_hidden, created_at, updated_at
      )
      VALUES (?, 'writing_mode', 'custom-camera', '自定义镜头', '镜头提示词', 0, 0, ?, ?)
      """,
      (project.id, project.created_at, project.updated_at),
    )
    await source.prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(
        name="导出续写模板",
        system_template="系统提示词",
        user_template="用户提示词 {input.chapters}",
        chapter_ids=[chapter.id],
        document_ids=[doc.id],
        config={"recent_chapter_enabled": True, "recent_chapter_count": 3},
      ),
    )
    await source.version_service.create_current_version(
      project.id,
      "chapter",
      "chapter-001",
      label="第一章版本",
      note="导出测试",
    )
    await source.version_service.create_current_version(
      project.id,
      "document",
      doc.id,
      label="资料版本",
      note="导出测试",
    )

    archive = await source.transfer_service.export_project(project.id, _default_options())
    assert b"source-secret" not in archive
    with zipfile.ZipFile(BytesIO(archive), "r") as zipped:
      names = zipped.namelist()
      manifest = json.loads(zipped.read("manifest.json"))
      assert "manifest.json" in names
      assert "data/documents.json" not in names
      assert "content/chapters/chapter-001.md" in names
      assert manifest["format_version"] == 2
      assert manifest["counts"]["documents"] == 0
      api_refs = json.loads(zipped.read("data/api_config_refs.json"))["rows"]
      assert api_refs[0]["api_key_configured"] == 1
      assert "api_key" not in api_refs[0]

    imported = await target.transfer_service.import_project(archive)
    assert imported.source_project_id == project.id
    assert imported.project.title == project.title
    assert imported.project.chapter_count == 2
    assert imported.warnings == [
      f"原 API 配置 {api_config.id} 在本机不存在，相关视角已设为默认配置。"
    ]

    imported_chapter = await target.chapter_service.get_chapter(
      imported.imported_project_id, "chapter-001"
    )
    assert imported_chapter.content == "第一章正文。\n\n雾从码头升起。"
    imported_tree = await target.chapter_service.list_chapter_tree(imported.imported_project_id)
    assert imported_tree[1].type == "folder"
    assert imported_tree[1].children[0].id == chapter.id

    imported_doc = await target.document_service.get_document(imported.imported_project_id, doc.id)
    assert imported_doc.content == "# 港口档案\n\n- 旧码头。"
    imported_perspectives = await target.perspective_service.list_perspectives(
      imported.imported_project_id
    )
    assert next(item for item in imported_perspectives if item.id == "pace-editor").api_config_id is None

    preset_row = await target.db.fetch_one(
      """
      SELECT content FROM generation_presets
      WHERE project_id = ? AND kind = 'writing_mode' AND preset_id = 'custom-camera'
      """,
      (imported.imported_project_id,),
    )
    assert preset_row and preset_row["content"] == "镜头提示词"
    profile = await target.prompt_profile_service.get_profile(
      imported.imported_project_id,
      "generate_next_paragraph",
    )
    assert profile.name == "导出续写模板"
    assert profile.chapter_ids == [chapter.id]
    chapter_versions = await target.version_service.list_versions(
      imported.imported_project_id,
      "chapter",
      "chapter-001",
    )
    assert chapter_versions[0].label == "第一章版本"
  finally:
    await source.store.shutdown()
    await target.store.shutdown()


@pytest.mark.asyncio
async def test_project_transfer_import_avoids_project_id_conflicts(tmp_path) -> None:
  stack = await _build_transfer_stack(tmp_path)
  try:
    project = await stack.project_service.create_project(CreateProjectRequest(title="Same Book"))
    archive = await stack.transfer_service.export_project(project.id, _default_options())
    imported = await stack.transfer_service.import_project(archive)
    assert imported.imported_project_id != project.id
    assert imported.imported_project_id.startswith(project.id)
    assert imported.project.title == "Same Book（导入副本）"
  finally:
    await stack.store.shutdown()


def test_project_transfer_rejects_unsafe_archive_path() -> None:
  buffer = BytesIO()
  with zipfile.ZipFile(buffer, "w") as archive:
    archive.writestr(
      "manifest.json",
      json.dumps(
        {
          "format": "deep-novel-typer.project-export",
          "format_version": 2,
          "exported_at": "2026-04-26T00:00:00+00:00",
          "source_project_id": "evil",
          "source_project_title": "evil",
        }
      ),
    )
    archive.writestr("checksums.json", "{}")
    archive.writestr("content/../evil.md", "bad")

  from app.Services.project_transfer.archive import read_project_archive

  with pytest.raises(InvalidProjectPathError):
    read_project_archive(buffer.getvalue())


def test_project_transfer_rejects_checksum_mismatch() -> None:
  buffer = BytesIO()
  with zipfile.ZipFile(buffer, "w") as archive:
    archive.writestr(
      "manifest.json",
      json.dumps(
        {
          "format": "deep-novel-typer.project-export",
          "format_version": 2,
          "exported_at": "2026-04-26T00:00:00+00:00",
          "source_project_id": "bad",
          "source_project_title": "bad",
        }
      ),
    )
    archive.writestr("checksums.json", json.dumps({"chapters/a.md": "wrong"}))
    archive.writestr("content/chapters/a.md", "content")

  from app.Services.project_transfer.archive import read_project_archive

  with pytest.raises(DomainError):
    read_project_archive(buffer.getvalue())


@pytest.mark.asyncio
async def test_project_transfer_cleanup_import_target_removes_directory(tmp_path) -> None:
  store = AsyncFileStore(tmp_path / "projects", max_workers=2)
  try:
    target_root = store.root / "half-imported"
    await store.write_text(target_root / "docs" / "outline.md", "partial")

    await cleanup_import_target(store, target_root)

    assert not await store.exists(target_root)
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_project_transfer_rejects_duplicate_document_node_id(tmp_path) -> None:
  source = await _build_transfer_stack(tmp_path / "source")
  target = await _build_transfer_stack(tmp_path / "target")
  try:
    project = await source.project_service.create_project(
      CreateProjectRequest(title="Duplicate Document Node Book")
    )
    archive = await source.transfer_service.export_project(project.id, _default_options())
    broken_archive = _archive_with_duplicate_document_node_id(archive)

    with pytest.raises(DomainError, match="duplicate document_nodes id"):
      await target.transfer_service.import_project(broken_archive)

    assert not await target.store.exists(target.store.root / project.id)
  finally:
    await source.store.shutdown()
    await target.store.shutdown()

@pytest.mark.asyncio
async def test_project_transfer_rejects_duplicate_chapter_node_id(tmp_path) -> None:
  source = await _build_transfer_stack(tmp_path / "source")
  target = await _build_transfer_stack(tmp_path / "target")
  try:
    project = await source.project_service.create_project(
      CreateProjectRequest(title="Duplicate Chapter Node Book")
    )
    archive = await source.transfer_service.export_project(project.id, _default_options())
    broken_archive = _archive_with_duplicate_chapter_node_id(archive)

    with pytest.raises(DomainError, match="duplicate chapter_nodes id"):
      await target.transfer_service.import_project(broken_archive)

    assert not await target.store.exists(target.store.root / project.id)
  finally:
    await source.store.shutdown()
    await target.store.shutdown()


class _TransferStack:
  def __init__(
    self,
    *,
    db: AsyncDatabase,
    store: AsyncFileStore,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    perspective_service: PerspectiveService,
    api_config_service: APIConfigService,
    prompt_profile_service: PromptProfileService,
    version_service: VersionService,
    transfer_service: ProjectTransferService,
  ) -> None:
    self.db = db
    self.store = store
    self.project_service = project_service
    self.chapter_service = chapter_service
    self.document_service = document_service
    self.perspective_service = perspective_service
    self.api_config_service = api_config_service
    self.prompt_profile_service = prompt_profile_service
    self.version_service = version_service
    self.transfer_service = transfer_service


async def _build_transfer_stack(tmp_path) -> _TransferStack:
  projects_dir = tmp_path / "projects"
  trash_dir = tmp_path / "trash"
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  store = AsyncFileStore(projects_dir, max_workers=2)
  paths = PathResolver(projects_dir, trash_dir)
  locks = AsyncLockRegistry()
  project_service = ProjectService(db, store, paths, locks)
  chapter_service = ChapterService(db, store, paths, locks, project_service)
  document_service = DocumentService(db, store, paths, locks, project_service)
  perspective_service = PerspectiveService(db, locks, project_service)
  api_config_service = APIConfigService(db, locks, _load_llm_settings())
  await api_config_service.ensure_default_config()
  prompt_profile_service = PromptProfileService(
    db,
    locks,
    project_service,
    chapter_service,
    document_service,
  )
  version_service = VersionService(
    db,
    store,
    paths,
    locks,
    project_service,
    chapter_service,
    document_service,
  )
  transfer_service = ProjectTransferService(db, store, paths, locks)
  return _TransferStack(
    db=db,
    store=store,
    project_service=project_service,
    chapter_service=chapter_service,
    document_service=document_service,
    perspective_service=perspective_service,
    api_config_service=api_config_service,
    prompt_profile_service=prompt_profile_service,
    version_service=version_service,
    transfer_service=transfer_service,
  )


def _default_options():
  from app.Schemas.project_transfer import ProjectExportOptions

  return ProjectExportOptions()


def _archive_with_duplicate_document_node_id(raw: bytes) -> bytes:
  source_buffer = BytesIO(raw)
  target_buffer = BytesIO()
  with zipfile.ZipFile(source_buffer, "r") as source_archive:
    with zipfile.ZipFile(
      target_buffer, "w", compression=zipfile.ZIP_DEFLATED
    ) as target_archive:
      for member in source_archive.infolist():
        content = source_archive.read(member.filename)
        if member.filename == "data/document_nodes.json":
          payload = json.loads(content.decode("utf-8"))
          duplicate = dict(payload["rows"][0])
          duplicate["title"] = "重复蓝图"
          payload["rows"].append(duplicate)
          content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        target_archive.writestr(member.filename, content)
  return target_buffer.getvalue()


def _archive_with_duplicate_chapter_node_id(raw: bytes) -> bytes:
  source_buffer = BytesIO(raw)
  target_buffer = BytesIO()
  with zipfile.ZipFile(source_buffer, "r") as source_archive:
    with zipfile.ZipFile(
      target_buffer, "w", compression=zipfile.ZIP_DEFLATED
    ) as target_archive:
      for member in source_archive.infolist():
        content = source_archive.read(member.filename)
        if member.filename == "data/chapter_nodes.json":
          payload = json.loads(content.decode("utf-8"))
          duplicate = dict(payload["rows"][0])
          duplicate["title"] = "重复节点"
          payload["rows"].append(duplicate)
          content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        target_archive.writestr(member.filename, content)
  return target_buffer.getvalue()
