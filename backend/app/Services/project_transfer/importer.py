from __future__ import annotations

from app.Services.project_transfer.archive import ProjectArchivePayload, read_project_archive
from app.Services.project_transfer.import_cleanup import cleanup_import_target
from app.Services.project_transfer.import_database import ProjectImportDatabaseWriter
from app.Services.project_transfer.import_files import write_content_files
from app.Services.project_transfer.import_validation import (
  counts_from_payload,
  required_object,
  rows,
  validate_expected_files,
  validate_unique_node_ids,
)
from app.Services.project_transfer.manifest import validate_manifest
from app.Utils.db import AsyncDatabase
from app.Utils.ids import slugify
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.project_transfer import ProjectImportResponse


class ProjectImporter:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
  ) -> None:
    self._store = store
    self._paths = paths
    self._database = ProjectImportDatabaseWriter(db, store, paths)

  async def import_project(self, raw: bytes) -> ProjectImportResponse:
    payload = read_project_archive(raw)
    validate_manifest(payload.manifest)
    source_project = required_object(payload.data, "project")
    source_project_id = str(
      source_project.get("id") or payload.manifest["source_project_id"]
    )
    source_title = str(
      source_project.get("title") or payload.manifest["source_project_title"]
    )
    required_object(payload.data, "document_nodes")
    validate_expected_files(payload)
    validate_unique_node_ids(payload)

    target_project_id = await self._database.next_project_id(
      slugify(source_title, fallback_prefix="book")
      if not source_project_id
      else source_project_id
    )
    title = (
      source_title
      if target_project_id == source_project_id
      else f"{source_title}（导入副本）"
    )
    target_root = self._paths.project(target_project_id).root
    warnings: list[str] = []

    try:
      await write_content_files(self._store, target_root, payload.content_files)
      project = await self._database.import_rows(
        payload=payload,
        source_project=source_project,
        target_project_id=target_project_id,
        target_title=title,
        target_root=target_root,
        warnings=warnings,
      )
      await self._store.write_json(
        target_root / "manifest.json",
        {
          **project.model_dump(mode="json"),
          "chapters": rows(payload, "chapters"),
          "documents": _workspace_documents_from_nodes(payload),
        },
      )
      return ProjectImportResponse(
        project=project,
        source_project_id=source_project_id,
        imported_project_id=target_project_id,
        warnings=warnings,
        counts=counts_from_payload(payload),
      )
    except Exception:
      await cleanup_import_target(self._store, target_root)
      raise


def _workspace_documents_from_nodes(payload: ProjectArchivePayload) -> list[dict[str, object]]:
  documents: list[dict[str, object]] = []
  for row in rows(payload, "document_nodes"):
    kind = str(row.get("id") or "")
    if kind not in {"outline", "design", "note"} or row.get("type") != "markdown":
      continue
    documents.append(
      {
        "kind": kind,
        "title": str(row.get("title") or ""),
        "updated_at": str(row.get("updated_at") or ""),
      }
    )
  order = {"outline": 1, "design": 2, "note": 3}
  return sorted(documents, key=lambda item: order.get(str(item["kind"]), 10))
