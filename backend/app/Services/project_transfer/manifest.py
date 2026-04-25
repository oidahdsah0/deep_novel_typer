from __future__ import annotations

from datetime import UTC, datetime

from app.Schemas.project_transfer import (
  ProjectExportManifest,
  ProjectExportOptions,
  ProjectTransferCounts,
)
from app.Utils.errors import DomainError

EXPORT_FORMAT = "deep-novel-typer.project-export"
EXPORT_FORMAT_VERSION = 2


def build_manifest(
  *,
  source_project_id: str,
  source_project_title: str,
  options: ProjectExportOptions,
  counts: ProjectTransferCounts,
) -> ProjectExportManifest:
  return ProjectExportManifest(
    format=EXPORT_FORMAT,
    format_version=EXPORT_FORMAT_VERSION,
    exported_at=datetime.now(tz=UTC).isoformat(),
    source_project_id=source_project_id,
    source_project_title=source_project_title,
    options=options,
    counts=counts,
  )


def validate_manifest(payload: dict[str, object]) -> None:
  if payload.get("format") != EXPORT_FORMAT:
    raise DomainError("Project import archive has an unsupported format")
  if payload.get("format_version") != EXPORT_FORMAT_VERSION:
    raise DomainError("Project import archive has an unsupported format version")
