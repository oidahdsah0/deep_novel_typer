from __future__ import annotations

import json

from app.Schemas.common import PromptProfileVersionType, PromptRequestType
from app.Schemas.prompt_profiles import (
  PromptProfile,
  PromptProfileSnapshot,
  PromptProfileVersion,
  PromptProfileVersionDetail,
)
from app.Services.prompt_profiles.contracts import (
  normalize_output_contract,
  normalize_prompt_template,
  output_contract,
)
from app.Services.prompt_profiles.defaults import DefaultPromptProfile
from app.Services.prompt_profiles.rendering import clean_id_list, json_list, json_object


def profile_from_default(default: DefaultPromptProfile) -> PromptProfile:
  return PromptProfile(
    request_type=default.request_type,
    name=default.name,
    system_template=normalize_prompt_template(default.request_type, default.system_template),
    user_template=normalize_prompt_template(default.request_type, default.user_template),
    output_contract=normalize_output_contract(
      default.request_type,
      output_contract(default.request_type),
    ),
    chapter_ids=list(default.chapter_ids),
    document_ids=list(default.document_ids),
    config=dict(default.config or {}),
    is_system=True,
  )


def profile_from_row(row: dict[str, object]) -> PromptProfile:
  request_type = row["request_type"]  # type: ignore[assignment]
  persisted_contract = str(row.get("output_contract") or "").strip()
  return PromptProfile(
    request_type=request_type,  # type: ignore[arg-type]
    name=str(row["name"]),
    system_template=normalize_prompt_template(
      request_type, str(row["system_template"])  # type: ignore[arg-type]
    ),
    user_template=normalize_prompt_template(
      request_type, str(row["user_template"])  # type: ignore[arg-type]
    ),
    output_contract=normalize_output_contract(request_type, persisted_contract),  # type: ignore[arg-type]
    chapter_ids=json_list(row["chapter_ids_json"]),
    document_ids=json_list(row["document_ids_json"]),
    config=json_object(row["config_json"]),
    is_system=bool(row["is_system"]),
    created_at=str(row["created_at"]),
    updated_at=str(row["updated_at"]),
  )


def profile_from_snapshot(
  request_type: PromptRequestType,
  snapshot: PromptProfileSnapshot,
  *,
  created_at: str,
  updated_at: str,
) -> PromptProfile:
  return PromptProfile(
    request_type=request_type,
    name=snapshot.name,
    system_template=normalize_prompt_template(request_type, snapshot.system_template),
    user_template=normalize_prompt_template(request_type, snapshot.user_template),
    output_contract=normalize_output_contract(request_type, snapshot.output_contract),
    chapter_ids=clean_id_list(snapshot.chapter_ids),
    document_ids=clean_id_list(snapshot.document_ids),
    config=dict(snapshot.config),
    is_system=False,
    created_at=created_at,
    updated_at=updated_at,
  )


def snapshot_from_profile(profile: PromptProfile) -> PromptProfileSnapshot:
  return PromptProfileSnapshot(
    name=profile.name,
    system_template=profile.system_template,
    user_template=profile.user_template,
    output_contract=normalize_output_contract(profile.request_type, profile.output_contract),
    chapter_ids=clean_id_list(profile.chapter_ids),
    document_ids=clean_id_list(profile.document_ids),
    config=dict(profile.config),
  )


def snapshot_from_json(value: object) -> PromptProfileSnapshot:
  try:
    payload = json.loads(str(value))
  except json.JSONDecodeError:
    payload = {}
  if not isinstance(payload, dict):
    payload = {}
  return PromptProfileSnapshot.model_validate(payload)


def version_from_row(row: dict[str, object]) -> PromptProfileVersion:
  snapshot = snapshot_from_json(row["snapshot_json"])
  return version_from_values(
    id=str(row["id"]),
    project_id=str(row["project_id"]),
    request_type=row["request_type"],  # type: ignore[arg-type]
    version_type=row["version_type"],  # type: ignore[arg-type]
    label=str(row["label"]) if row["label"] is not None else None,
    note=str(row["note"] or ""),
    snapshot=snapshot,
    created_at=str(row["created_at"]),
  )


def version_detail_from_row(row: dict[str, object]) -> PromptProfileVersionDetail:
  snapshot = snapshot_from_json(row["snapshot_json"])
  return version_detail_from_values(
    id=str(row["id"]),
    project_id=str(row["project_id"]),
    request_type=row["request_type"],  # type: ignore[arg-type]
    version_type=row["version_type"],  # type: ignore[arg-type]
    label=str(row["label"]) if row["label"] is not None else None,
    note=str(row["note"] or ""),
    snapshot=snapshot,
    created_at=str(row["created_at"]),
  )


def version_from_values(
  *,
  id: str,
  project_id: str,
  request_type: PromptRequestType,
  version_type: PromptProfileVersionType,
  label: str | None,
  note: str,
  snapshot: PromptProfileSnapshot,
  created_at: str,
) -> PromptProfileVersion:
  return PromptProfileVersion(
    id=id,
    project_id=project_id,
    request_type=request_type,
    version_type=version_type,
    label=label,
    note=note,
    system_chars=len(snapshot.system_template),
    user_chars=len(snapshot.user_template),
    chapter_count=len(snapshot.chapter_ids),
    document_count=len(snapshot.document_ids),
    created_at=created_at,
  )


def version_detail_from_values(
  *,
  id: str,
  project_id: str,
  request_type: PromptRequestType,
  version_type: PromptProfileVersionType,
  label: str | None,
  note: str,
  snapshot: PromptProfileSnapshot,
  created_at: str,
) -> PromptProfileVersionDetail:
  return PromptProfileVersionDetail(
    **version_from_values(
      id=id,
      project_id=project_id,
      request_type=request_type,
      version_type=version_type,
      label=label,
      note=note,
      snapshot=snapshot,
      created_at=created_at,
    ).model_dump(),
    snapshot=snapshot,
  )
