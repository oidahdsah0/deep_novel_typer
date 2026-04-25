from __future__ import annotations

from typing import Any

from app.Services.project_transfer.archive import ProjectArchivePayload, safe_relative_path
from app.Utils.errors import DomainError
from app.Schemas.project_transfer import ProjectTransferCounts


def rows(payload: ProjectArchivePayload, key: str) -> list[dict[str, Any]]:
  value = payload.data.get(key)
  if isinstance(value, dict):
    row_values = value.get("rows", [])
  else:
    row_values = value or []
  if not isinstance(row_values, list):
    raise DomainError(f"Project import archive data/{key}.json rows must be a list")
  return [row for row in row_values if isinstance(row, dict)]


def required_object(data: dict[str, Any], key: str) -> dict[str, Any]:
  value = data.get(key)
  if not isinstance(value, dict):
    raise DomainError(f"Project import archive is missing data/{key}.json")
  return value


def with_project_id(
  row: dict[str, Any],
  project_id: str,
  *,
  extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
  next_row = dict(row)
  next_row["project_id"] = project_id
  if extra:
    next_row.update(extra)
  return next_row


def import_value(table: str, row: dict[str, Any], column: str) -> Any:
  if table == "chapters" and column == "writing_synopsis":
    return row.get(column) or ""
  if table == "chapters" and column == "writing_synopsis_updated_at":
    return row.get(column) or row.get("updated_at") or ""
  if table == "prompt_profiles" and column == "output_contract":
    return row.get(column) or ""
  return row.get(column)


def counts_from_payload(payload: ProjectArchivePayload) -> ProjectTransferCounts:
  return ProjectTransferCounts(
    chapters=len(rows(payload, "chapters")),
    documents=0,
    chapter_nodes=len(rows(payload, "chapter_nodes")),
    document_nodes=len(rows(payload, "document_nodes")),
    perspectives=len(rows(payload, "perspectives")),
    generation_presets=len(rows(payload, "generation_presets")),
    prompt_profiles=len(rows(payload, "prompt_profiles")),
    prompt_profile_versions=len(rows(payload, "prompt_profile_versions")),
    resource_versions=len(rows(payload, "resource_versions")),
    debug_logs=len(rows(payload, "debug_logs")),
    token_usage_rows=len(rows(payload, "token_usage")),
  )


def validate_expected_files(payload: ProjectArchivePayload) -> None:
  expected: set[str] = set()
  for row in rows(payload, "chapters"):
    expected.add(safe_relative_path(row["file_path"]))
  for row in rows(payload, "document_nodes"):
    if row.get("file_path"):
      expected.add(safe_relative_path(row["file_path"]))
  for row in rows(payload, "resource_versions"):
    expected.add(safe_relative_path(row["file_path"]))
  missing = sorted(path for path in expected if path not in payload.content_files)
  if missing:
    raise DomainError(f"Project import archive is missing content file: {missing[0]}")


def validate_unique_node_ids(payload: ProjectArchivePayload) -> None:
  for table in ("chapter_nodes", "document_nodes"):
    seen: set[str] = set()
    for row in rows(payload, table):
      node_id = str(row.get("id") or "").strip()
      if not node_id:
        raise DomainError(
          f"Project import archive contains a {table} row without id"
        )
      if node_id in seen:
        raise DomainError(
          f"Project import archive contains duplicate {table} id: {node_id}"
        )
      seen.add(node_id)
