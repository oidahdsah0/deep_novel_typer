from __future__ import annotations

import math

REQUEST_API_CONFIG_ID_KEY = "api_config_id"
REQUEST_TEMPERATURE_KEY = "temperature"
INCLUDE_CHAPTER_SYNOPSIS_KEY = "include_chapter_synopsis"
DEFAULT_INCLUDE_CHAPTER_SYNOPSIS = True


def api_config_id_from_config(config: dict[str, object] | None) -> str | None:
  if not config:
    return None
  value = config.get(REQUEST_API_CONFIG_ID_KEY)
  if not isinstance(value, str):
    return None
  stripped = value.strip()
  return stripped or None


def temperature_from_config(config: dict[str, object] | None) -> float | None:
  if not config or REQUEST_TEMPERATURE_KEY not in config:
    return None
  try:
    return normalize_temperature(config.get(REQUEST_TEMPERATURE_KEY))
  except ValueError:
    return None


def normalize_temperature(value: object) -> float | None:
  if value is None:
    return None
  if isinstance(value, str):
    stripped = value.strip()
    if not stripped:
      return None
    try:
      parsed = float(stripped)
    except ValueError as exc:
      raise ValueError("Temperature must be a number.") from exc
  elif isinstance(value, bool):
    raise ValueError("Temperature must be a number.")
  elif isinstance(value, int | float):
    parsed = float(value)
  else:
    raise ValueError("Temperature must be a number.")
  if not math.isfinite(parsed) or parsed < 0 or parsed > 2:
    raise ValueError("Temperature must be between 0 and 2.")
  return parsed


def normalize_temperature_in_config(config: dict[str, object]) -> dict[str, object]:
  normalized = dict(config)
  if REQUEST_TEMPERATURE_KEY not in normalized:
    return normalized
  temperature = normalize_temperature(normalized.get(REQUEST_TEMPERATURE_KEY))
  if temperature is None:
    normalized.pop(REQUEST_TEMPERATURE_KEY, None)
  else:
    normalized[REQUEST_TEMPERATURE_KEY] = temperature
  return normalized


def include_chapter_synopsis_from_config(config: dict[str, object] | None) -> bool:
  if not config or INCLUDE_CHAPTER_SYNOPSIS_KEY not in config:
    return DEFAULT_INCLUDE_CHAPTER_SYNOPSIS
  return config.get(INCLUDE_CHAPTER_SYNOPSIS_KEY) is not False
