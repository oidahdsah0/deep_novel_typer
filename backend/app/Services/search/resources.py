from __future__ import annotations

import json

from app.Services.prompt_profiles.contracts import output_contract
from app.Services.prompt_profiles.defaults import DEFAULT_PROFILES, REQUEST_TYPES
from app.Services.search.indexing import SearchDocument
from app.Services.search.labels import (
  PRESET_LABELS,
  PROMPT_LABELS,
  VERSION_RESOURCE_LABELS,
)
from app.Utils.config import GenerationPresetDefault
from app.Utils.db import AsyncDatabase
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.search import (
  ProjectSearchMatch,
  ProjectSearchResourceType,
  ProjectSearchResult,
)


class ProjectSearchResourceBuilder:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    generation_defaults: tuple[GenerationPresetDefault, ...],
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths
    self._generation_defaults = generation_defaults

  async def build_documents(
    self,
    project_id: str,
    meta: dict[tuple[str, str], dict[str, object]],
    expected: set[tuple[str, str]],
  ) -> list[SearchDocument]:
    documents: list[SearchDocument] = []
    documents.extend(await self._chapter_documents(project_id, meta, expected))
    documents.extend(await self._document_documents(project_id, meta, expected))
    documents.extend(await self._prompt_profile_documents(project_id, meta, expected))
    documents.extend(await self._prompt_version_documents(project_id, meta, expected))
    documents.extend(await self._generation_preset_documents(project_id, meta, expected))
    documents.extend(await self._resource_version_documents(project_id, meta, expected))
    return documents

  async def _chapter_documents(
    self,
    project_id: str,
    meta: dict[tuple[str, str], dict[str, object]],
    expected: set[tuple[str, str]],
  ) -> list[SearchDocument]:
    rows = await self._db.fetch_all(
      """
      SELECT c.id, c.title, c.file_path, c.updated_at, n.id AS node_id, n.parent_id
      FROM chapters c
      JOIN chapter_nodes n ON n.project_id = c.project_id AND n.chapter_id = c.id
      WHERE c.project_id = ?
      ORDER BY c.order_index ASC
      """,
      (project_id,),
    )
    node_rows = await self._db.fetch_all(
      """
      SELECT id, parent_id, type, title
      FROM chapter_nodes
      WHERE project_id = ?
      ORDER BY order_index ASC
      """,
      (project_id,),
    )
    paths = node_paths(node_rows, leaf_type="chapter")
    documents: list[SearchDocument] = []
    root = self._paths.project(project_id).root
    for row in rows:
      chapter_id = str(row["id"])
      node_id = str(row["node_id"])
      path = paths.get(node_id, [])
      expected.add(("chapter", chapter_id))
      if meta_is_current(meta.get(("chapter", chapter_id)), str(row["title"]), path, str(row["updated_at"])):
        continue
      content_path = root / str(row["file_path"])
      if not await self._store.exists(content_path):
        continue
      documents.append(
        SearchDocument(
          project_id=project_id,
          resource_type="chapter",
          resource_id=chapter_id,
          resource_subtype="chapter",
          title=str(row["title"]),
          path=path,
          body=await self._store.read_text(content_path),
          updated_at=str(row["updated_at"]),
          metadata={"chapter_id": chapter_id, "node_id": node_id},
        )
      )
    return documents

  async def _document_documents(
    self,
    project_id: str,
    meta: dict[tuple[str, str], dict[str, object]],
    expected: set[tuple[str, str]],
  ) -> list[SearchDocument]:
    rows = await self._db.fetch_all(
      """
      SELECT id, parent_id, type, title, file_path, updated_at
      FROM document_nodes
      WHERE project_id = ?
      ORDER BY order_index ASC
      """,
      (project_id,),
    )
    paths = node_paths(rows, leaf_type="markdown")
    documents: list[SearchDocument] = []
    root = self._paths.project(project_id).root
    for row in rows:
      if str(row["type"]) != "markdown":
        continue
      document_id = str(row["id"])
      path = paths.get(document_id, [])
      expected.add(("document", document_id))
      if meta_is_current(meta.get(("document", document_id)), str(row["title"]), path, str(row["updated_at"])):
        continue
      if not row["file_path"]:
        continue
      content_path = root / str(row["file_path"])
      if not await self._store.exists(content_path):
        continue
      documents.append(
        SearchDocument(
          project_id=project_id,
          resource_type="document",
          resource_id=document_id,
          resource_subtype="markdown",
          title=str(row["title"]),
          path=path,
          body=await self._store.read_text(content_path),
          updated_at=str(row["updated_at"]),
          metadata={"document_id": document_id, "node_id": document_id},
        )
      )
    return documents

  async def _prompt_profile_documents(
    self,
    project_id: str,
    meta: dict[tuple[str, str], dict[str, object]],
    expected: set[tuple[str, str]],
  ) -> list[SearchDocument]:
    rows = await self._db.fetch_all(
      """
      SELECT request_type, name, system_template, user_template, output_contract, config_json, updated_at
      FROM prompt_profiles
      WHERE project_id = ?
      """,
      (project_id,),
    )
    overrides = {str(row["request_type"]): row for row in rows}
    documents: list[SearchDocument] = []
    for request_type in REQUEST_TYPES:
      row = overrides.get(request_type)
      if row is None:
        default = DEFAULT_PROFILES[request_type]
        name = default.name
        system_template = default.system_template
        user_template = default.user_template
        contract = output_contract(request_type)
        config_json = json.dumps(default.config or {}, ensure_ascii=False, sort_keys=True)
        updated_at = "default"
      else:
        name = str(row["name"])
        system_template = str(row["system_template"])
        user_template = str(row["user_template"])
        contract = str(row["output_contract"])
        config_json = str(row["config_json"])
        updated_at = str(row["updated_at"])

      expected.add(("prompt_profile", request_type))
      document = SearchDocument(
        project_id=project_id,
        resource_type="prompt_profile",
        resource_id=request_type,
        resource_subtype=request_type,
        title=name,
        path=["请求配置", PROMPT_LABELS.get(request_type, request_type)],
        body="\n\n".join([system_template, user_template, contract, config_json]),
        updated_at=updated_at,
        metadata={"request_type": request_type},
      )
      if not document_is_current(meta.get(("prompt_profile", request_type)), document):
        documents.append(document)
    return documents

  async def _prompt_version_documents(
    self,
    project_id: str,
    meta: dict[tuple[str, str], dict[str, object]],
    expected: set[tuple[str, str]],
  ) -> list[SearchDocument]:
    rows = await self._db.fetch_all(
      """
      SELECT id, request_type, version_type, label, note, snapshot_json, created_at
      FROM prompt_profile_versions
      WHERE project_id = ?
      ORDER BY created_at DESC
      """,
      (project_id,),
    )
    documents: list[SearchDocument] = []
    for row in rows:
      version_id = str(row["id"])
      request_type = str(row["request_type"])
      expected.add(("prompt_profile_version", version_id))
      title = str(row["label"] or PROMPT_LABELS.get(request_type, request_type))
      document = SearchDocument(
        project_id=project_id,
        resource_type="prompt_profile_version",
        resource_id=version_id,
        resource_subtype=request_type,
        title=title,
        path=["请求历史", PROMPT_LABELS.get(request_type, request_type)],
        body="\n\n".join([str(row["note"] or ""), str(row["snapshot_json"] or "")]),
        updated_at=str(row["created_at"]),
        metadata={
          "request_type": request_type,
          "version_id": version_id,
          "version_type": str(row["version_type"]),
        },
      )
      if not document_is_current(meta.get(("prompt_profile_version", version_id)), document):
        documents.append(document)
    return documents

  async def _generation_preset_documents(
    self,
    project_id: str,
    meta: dict[tuple[str, str], dict[str, object]],
    expected: set[tuple[str, str]],
  ) -> list[SearchDocument]:
    rows = await self._db.fetch_all(
      """
      SELECT kind, preset_id, name, content, is_system, is_hidden, updated_at
      FROM generation_presets
      WHERE project_id = ?
      """,
      (project_id,),
    )
    overrides = {
      (str(row["kind"]), str(row["preset_id"])): row
      for row in rows
    }
    documents: list[SearchDocument] = []

    for default in self._generation_defaults:
      key = (default.kind, default.preset_id)
      row = overrides.pop(key, None)
      if row is not None and bool(row["is_hidden"]):
        continue
      document = generation_preset_document(
        project_id,
        default.kind,
        default.preset_id,
        str(row["name"]) if row else default.name,
        str(row["content"]) if row else default.content,
        str(row["updated_at"]) if row else "default",
      )
      expected.add(("generation_preset", document.resource_id))
      if not document_is_current(meta.get(("generation_preset", document.resource_id)), document):
        documents.append(document)

    for row in overrides.values():
      if bool(row["is_hidden"]):
        continue
      document = generation_preset_document(
        project_id,
        str(row["kind"]),
        str(row["preset_id"]),
        str(row["name"]),
        str(row["content"]),
        str(row["updated_at"]),
      )
      expected.add(("generation_preset", document.resource_id))
      if not document_is_current(meta.get(("generation_preset", document.resource_id)), document):
        documents.append(document)

    return documents

  async def _resource_version_documents(
    self,
    project_id: str,
    meta: dict[tuple[str, str], dict[str, object]],
    expected: set[tuple[str, str]],
  ) -> list[SearchDocument]:
    rows = await self._db.fetch_all(
      """
      SELECT id, resource_type, resource_id, resource_title, version_type,
             label, note, file_path, created_at
      FROM resource_versions
      WHERE project_id = ?
      ORDER BY created_at DESC
      """,
      (project_id,),
    )
    root = self._paths.project(project_id).root
    documents: list[SearchDocument] = []
    for row in rows:
      version_id = str(row["id"])
      expected.add(("resource_version", version_id))
      title = str(row["label"] or row["resource_title"])
      path = [
        "历史版本",
        VERSION_RESOURCE_LABELS.get(str(row["resource_type"]), str(row["resource_type"])),
        str(row["resource_title"]),
      ]
      if meta_is_current(meta.get(("resource_version", version_id)), title, path, str(row["created_at"])):
        continue
      file_path = root / str(row["file_path"])
      if not await self._store.exists(file_path):
        continue
      documents.append(
        SearchDocument(
          project_id=project_id,
          resource_type="resource_version",
          resource_id=version_id,
          resource_subtype=str(row["resource_type"]),
          title=title,
          path=path,
          body="\n\n".join([str(row["note"] or ""), await self._store.read_text(file_path)]),
          updated_at=str(row["created_at"]),
          metadata={
            "version_id": version_id,
            "resource_type": str(row["resource_type"]),
            "resource_id": str(row["resource_id"]),
            "version_type": str(row["version_type"]),
          },
        )
      )
    return documents


def generation_preset_document(
  project_id: str,
  kind: str,
  preset_id: str,
  name: str,
  content: str,
  updated_at: str,
) -> SearchDocument:
  resource_id = f"{kind}:{preset_id}"
  return SearchDocument(
    project_id=project_id,
    resource_type="generation_preset",
    resource_id=resource_id,
    resource_subtype=kind,
    title=name,
    path=["生成预设", PRESET_LABELS.get(kind, kind)],
    body=content,
    updated_at=updated_at,
    metadata={"kind": kind, "preset_id": preset_id},
  )


def search_result_from_row(row: dict[str, object]) -> ProjectSearchResult:
  matches = [
    ProjectSearchMatch(field="title", snippet=str(row["title_snippet"]))
    for _ in [0]
    if row.get("title_snippet")
  ]
  if row.get("path_snippet"):
    matches.append(ProjectSearchMatch(field="path", snippet=str(row["path_snippet"])))
  if row.get("content_snippet"):
    content_snippet = str(row["content_snippet"])
    if content_snippet not in {match.snippet for match in matches}:
      matches.append(ProjectSearchMatch(field="content", snippet=content_snippet))
  return ProjectSearchResult(
    resource_type=row["resource_type"],  # type: ignore[arg-type]
    resource_id=str(row["resource_id"]),
    resource_subtype=str(row["resource_subtype"] or ""),
    title=str(row["title"]),
    path=split_path(str(row["path_text"] or "")),
    updated_at=str(row["updated_at"]),
    score=float(row["score"] or 0),
    matches=matches,
    metadata=row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
  )


def stale_resources(
  meta_rows: list[dict[str, object]], expected: set[tuple[str, str]]
) -> list[tuple[ProjectSearchResourceType, str]]:
  stale: list[tuple[ProjectSearchResourceType, str]] = []
  for row in meta_rows:
    resource_type = str(row["resource_type"])
    resource_id = str(row["resource_id"])
    if (resource_type, resource_id) not in expected:
      stale.append((resource_type, resource_id))  # type: ignore[arg-type]
  return stale


def node_paths(rows: list[dict[str, object]], leaf_type: str) -> dict[str, list[str]]:
  nodes = {str(row["id"]): row for row in rows}
  paths: dict[str, list[str]] = {}
  for node_id, row in nodes.items():
    if str(row["type"]) != leaf_type:
      continue
    path: list[str] = []
    parent_id = row["parent_id"]
    while parent_id and str(parent_id) in nodes:
      parent = nodes[str(parent_id)]
      path.append(str(parent["title"]))
      parent_id = parent["parent_id"]
    paths[node_id] = list(reversed(path))
  return paths


def meta_is_current(
  meta_row: dict[str, object] | None,
  title: str,
  path: list[str],
  updated_at: str,
) -> bool:
  if meta_row is None:
    return False
  return (
    str(meta_row["title"]) == title
    and str(meta_row["path_text"]) == " / ".join(path)
    and str(meta_row["updated_at"]) == updated_at
  )


def document_is_current(meta_row: dict[str, object] | None, document: SearchDocument) -> bool:
  if meta_row is None:
    return False
  return (
    str(meta_row["title"]) == document.title
    and str(meta_row["path_text"]) == document.path_text
    and str(meta_row["updated_at"]) == document.updated_at
    and str(meta_row["content_hash"]) == document.content_hash
  )


def split_path(path_text: str) -> list[str]:
  return [item.strip() for item in path_text.split("/") if item.strip()]
