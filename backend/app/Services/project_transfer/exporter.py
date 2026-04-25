from __future__ import annotations

import json
from typing import Any

from app.Services.debug_readable import build_debug_readable_view
from app.Services.project_transfer.archive import ProjectArchiveBuilder, safe_relative_path
from app.Services.project_transfer.manifest import build_manifest
from app.Utils.db import AsyncDatabase
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.project_transfer import ProjectExportOptions, ProjectTransferCounts


class ProjectExporter:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths

  async def export_project(self, project_id: str, options: ProjectExportOptions) -> bytes:
    project = await self._require_project(project_id)
    chapters = await self._rows("chapters", "project_id = ?", (project_id,), "order_index ASC")
    chapter_nodes = await self._rows(
      "chapter_nodes",
      "project_id = ?",
      (project_id,),
      "parent_id ASC, order_index ASC, title ASC",
    )
    document_nodes = await self._rows(
      "document_nodes",
      "project_id = ?",
      (project_id,),
      "parent_id ASC, order_index ASC, title ASC",
    )
    perspectives = await self._rows(
      "perspectives", "project_id = ?", (project_id,), "created_at ASC, name ASC"
    )
    generation_presets = await self._rows(
      "generation_presets", "project_id = ?", (project_id,), "kind ASC, updated_at ASC"
    )
    prompt_profiles = await self._rows(
      "prompt_profiles", "project_id = ?", (project_id,), "request_type ASC"
    )
    prompt_profile_versions = await self._rows(
      "prompt_profile_versions",
      "project_id = ?",
      (project_id,),
      "request_type ASC, created_at DESC",
    )
    resource_versions = await self._rows(
      "resource_versions",
      "project_id = ?",
      (project_id,),
      "resource_type ASC, resource_id ASC, created_at DESC",
    )
    debug_logs = (
      await self._debug_logs(project_id)
      if options.include_debug_logs
      else []
    )
    token_usage = (
      await self._rows(
        "model_token_usage_daily",
        "project_id = ?",
        (project_id,),
        "date DESC, model_kind ASC, request_type ASC",
      )
      if options.include_token_usage
      else []
    )
    api_config_refs = (
      await self._api_config_refs(perspectives)
      if options.include_api_config_summary
      else []
    )

    counts = ProjectTransferCounts(
      chapters=len(chapters),
      documents=0,
      chapter_nodes=len(chapter_nodes),
      document_nodes=len(document_nodes),
      perspectives=len(perspectives),
      generation_presets=len(generation_presets),
      prompt_profiles=len(prompt_profiles),
      prompt_profile_versions=len(prompt_profile_versions),
      resource_versions=len(resource_versions),
      debug_logs=len(debug_logs),
      token_usage_rows=len(token_usage),
    )
    manifest = build_manifest(
      source_project_id=project_id,
      source_project_title=str(project["title"]),
      options=options,
      counts=counts,
    )
    builder = ProjectArchiveBuilder()
    builder.add_json("manifest.json", manifest.model_dump(mode="json"))
    builder.add_json("data/project.json", _json_safe(project))
    builder.add_json("data/chapters.json", {"rows": _json_safe(chapters)})
    builder.add_json("data/chapter_nodes.json", {"rows": _json_safe(chapter_nodes)})
    builder.add_json("data/document_nodes.json", {"rows": _json_safe(document_nodes)})
    builder.add_json("data/perspectives.json", {"rows": _json_safe(perspectives)})
    builder.add_json("data/api_config_refs.json", {"rows": _json_safe(api_config_refs)})
    builder.add_json("data/generation_presets.json", {"rows": _json_safe(generation_presets)})
    builder.add_json("data/prompt_profiles.json", {"rows": _json_safe(prompt_profiles)})
    builder.add_json(
      "data/prompt_profile_versions.json",
      {"rows": _json_safe(prompt_profile_versions)},
    )
    builder.add_json("data/resource_versions.json", {"rows": _json_safe(resource_versions)})
    if options.include_debug_logs:
      builder.add_json("data/debug_logs.json", {"rows": _json_safe(debug_logs)})
    if options.include_token_usage:
      builder.add_json("data/token_usage.json", {"rows": _json_safe(token_usage)})

    await self._add_project_files(builder, project_id, chapters, document_nodes, resource_versions)
    return builder.build()

  async def _require_project(self, project_id: str) -> dict[str, Any]:
    row = await self._db.fetch_one(
      """
      SELECT id, title, subtitle, description, genre, status, root_path,
             created_at, updated_at, last_opened_at, deleted_at
      FROM projects
      WHERE id = ? AND deleted_at IS NULL
      """,
      (project_id,),
    )
    if row is None:
      from app.Utils.errors import EntityNotFoundError

      raise EntityNotFoundError(f"Project not found: {project_id}")
    return row

  async def _rows(
    self,
    table: str,
    where: str,
    params: tuple[object, ...],
    order_by: str,
  ) -> list[dict[str, Any]]:
    return await self._db.fetch_all(
      f"SELECT * FROM {table} WHERE {where} ORDER BY {order_by}",
      params,
    )

  async def _api_config_refs(self, perspectives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    config_ids = sorted(
      {
        str(row["api_config_id"])
        for row in perspectives
        if row.get("api_config_id")
      }
    )
    if not config_ids:
      return []
    placeholders = ", ".join("?" for _ in config_ids)
    rows = await self._db.fetch_all(
      f"""
      SELECT id, name, provider, kind, protocol, api_key_required, base_url,
             mode, model, thinking_enabled, reasoning_effort, max_tokens,
             context_window_tokens, temperature, top_p, top_k, dimensions,
             is_default, created_at, updated_at,
             CASE WHEN api_key IS NULL OR api_key = '' THEN 0 ELSE 1 END AS api_key_configured
      FROM api_configs
      WHERE id IN ({placeholders})
      ORDER BY id ASC
      """,
      tuple(config_ids),
    )
    return rows

  async def _debug_logs(self, project_id: str) -> list[dict[str, Any]]:
    rows = await self._rows(
      "model_request_logs",
      "project_id = ?",
      (project_id,),
      "created_at DESC, id DESC",
    )
    sanitized: list[dict[str, Any]] = []
    for row in rows:
      request_body = _loads(row.get("request_body_json"))
      response_body = _loads(row.get("response_body_json"))
      context_pack = _loads(row.get("context_pack_json"))
      error_message = str(row["error_message"]) if row.get("error_message") else None
      readable = build_debug_readable_view(
        request_body=request_body,
        response_body=response_body,
        context_pack=context_pack,
        error_message=error_message,
        request_type=str(row.get("request_type") or ""),
        model_kind=str(row.get("model_kind") or "llm"),
      )
      next_row = dict(row)
      next_row["request_body_json"] = json.dumps(_export_request_body(row, request_body, readable), ensure_ascii=False)
      next_row["debug_readable"] = readable.model_dump(mode="json")
      sanitized.append(next_row)
    return sanitized

  async def _add_project_files(
    self,
    builder: ProjectArchiveBuilder,
    project_id: str,
    chapters: list[dict[str, Any]],
    document_nodes: list[dict[str, Any]],
    resource_versions: list[dict[str, Any]],
  ) -> None:
    project_root = self._paths.project(project_id).root
    paths: set[str] = set()
    for row in chapters:
      paths.add(safe_relative_path(row["file_path"]))
    for row in document_nodes:
      if row.get("file_path"):
        paths.add(safe_relative_path(row["file_path"]))
    for row in resource_versions:
      paths.add(safe_relative_path(row["file_path"]))

    for relative_path in sorted(paths):
      path = project_root / relative_path
      if await self._store.exists(path):
        builder.add_content_text(relative_path, await self._store.read_text(path))


def _loads(value: object) -> dict[str, Any]:
  try:
    payload = json.loads(str(value or "{}"))
  except json.JSONDecodeError:
    return {}
  return payload if isinstance(payload, dict) else {}


def _export_request_body(
  row: dict[str, Any],
  request_body: dict[str, Any],
  readable,
) -> dict[str, Any]:
  if str(row.get("model_kind") or "llm") == "embedding":
    return dict(readable.request_options)
  return readable.request_options | {"messages": request_body.get("messages", [])}


def _json_safe(value: Any) -> Any:
  if value is None or isinstance(value, (str, int, float, bool)):
    return value
  if isinstance(value, dict):
    return {str(key): _json_safe(item) for key, item in value.items()}
  if isinstance(value, list):
    return [_json_safe(item) for item in value]
  return str(value)
