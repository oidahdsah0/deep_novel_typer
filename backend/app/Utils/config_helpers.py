from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.Utils.config_types import LLM_MODE_NON_STREAM


def _split_csv(value: str) -> list[str]:
  return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str | None, default: bool = False) -> bool:
  if value is None:
    return default
  return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_bool(value: object, default: bool = False) -> bool:
  if isinstance(value, bool):
    return value
  if isinstance(value, str):
    return _parse_bool(value, default)
  return default


def _read_yaml(path: Path) -> dict[str, Any]:
  if not path.exists():
    return {}
  payload = yaml.safe_load(path.read_text(encoding="utf-8"))
  return payload if isinstance(payload, dict) else {}


def _dict(value: object) -> dict[str, Any]:
  return value if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, Any]]:
  if not isinstance(value, list):
    return []
  return [item for item in value if isinstance(item, dict)]


def _preset_id(item: dict[str, Any], fallback: str) -> str:
  value = str(item.get("id") or "").strip()
  return value or fallback


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
  merged = dict(base)
  for key, value in override.items():
    if isinstance(value, dict) and isinstance(merged.get(key), dict):
      merged[key] = _deep_merge(merged[key], value)
    else:
      merged[key] = value
  return merged


def _common_request_options(request_payload: dict[str, Any]) -> dict[str, Any]:
  if any(key in request_payload for key in ("common", LLM_MODE_NON_STREAM)):
    return _dict(request_payload.get("common"))
  return request_payload


def _default_llm_request() -> dict[str, Any]:
  return {
    "thinking": {"type": "enabled"},
    "reasoning_effort": "high",
    "max_tokens": 4096,
    "response_format": {"type": "json_object"},
    "stream": False,
  }
