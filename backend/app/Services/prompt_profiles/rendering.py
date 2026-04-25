from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.Schemas.prompt_preview import PromptPreviewMaterial, PromptPreviewProfileOverride
from app.Schemas.prompt_context import PromptContextPack
from app.Schemas.prompt_profiles import PromptProfile
from app.Services.prompt_profiles.contracts import (
  normalize_output_contract,
  normalize_prompt_template,
  output_contract,
)
from app.Utils.llm import LLMMessage


PLACEHOLDER_RE = re.compile(r"\{input\.([a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass(frozen=True)
class PromptProfileBuildResult:
  messages: list[LLMMessage]
  chapters: list[PromptPreviewMaterial]
  documents: list[PromptPreviewMaterial]
  context_pack: PromptContextPack | None = None


def apply_profile_override(
  profile: PromptProfile, override: PromptPreviewProfileOverride
) -> PromptProfile:
  return PromptProfile(
    request_type=profile.request_type,
    name=override.name if override.name is not None else profile.name,
    system_template=normalize_prompt_template(
      profile.request_type,
      override.system_template
      if override.system_template is not None
      else profile.system_template,
    ),
    user_template=normalize_prompt_template(
      profile.request_type,
      override.user_template if override.user_template is not None else profile.user_template,
    ),
    output_contract=normalize_output_contract(
      profile.request_type,
      override.output_contract
      if override.output_contract is not None
      else profile.output_contract or output_contract(profile.request_type),
    ),
    chapter_ids=(
      clean_id_list(override.chapter_ids)
      if override.chapter_ids is not None
      else profile.chapter_ids
    ),
    document_ids=(
      clean_id_list(override.document_ids)
      if override.document_ids is not None
      else profile.document_ids
    ),
    config=override.config if override.config is not None else profile.config,
    is_system=profile.is_system,
    created_at=profile.created_at,
    updated_at=profile.updated_at,
  )


def render_template(template: str, input_values: dict[str, str]) -> str:
  def replace(match: re.Match[str]) -> str:
    key = match.group(1)
    return input_values.get(key, match.group(0))

  return PLACEHOLDER_RE.sub(replace, template)


def format_runtime_value(value: object) -> str:
  if value is None:
    return ""
  if isinstance(value, str):
    return value
  if isinstance(value, (dict, list)):
    return json.dumps(value, ensure_ascii=False, indent=2)
  return str(value)


def json_list(value: object) -> list[str]:
  try:
    payload = json.loads(str(value))
  except json.JSONDecodeError:
    return []
  return clean_id_list(payload if isinstance(payload, list) else [])


def json_object(value: object) -> dict[str, object]:
  try:
    payload = json.loads(str(value))
  except json.JSONDecodeError:
    return {}
  return payload if isinstance(payload, dict) else {}


def clean_id_list(values: object) -> list[str]:
  if not isinstance(values, list):
    return []
  result: list[str] = []
  seen: set[str] = set()
  for value in values:
    if not isinstance(value, str):
      continue
    clean = value.strip()
    if not clean or clean in seen or len(clean) > 160:
      continue
    seen.add(clean)
    result.append(clean)
  return result[:500]


def truncate(value: str, limit: int) -> str:
  if len(value) <= limit:
    return value
  head_length = max(0, limit // 2)
  tail_length = max(0, limit - head_length - 32)
  return f"{value[:head_length]}\n\n[...内容过长，已省略中段...]\n\n{value[-tail_length:]}"
