from __future__ import annotations

import os
from pathlib import Path

from app.Utils.config_helpers import (
  _as_bool,
  _common_request_options,
  _deep_merge,
  _default_llm_request,
  _dict,
  _parse_bool,
  _read_yaml,
)
from app.Utils.config_types import LLM_MODE_NON_STREAM, LLMSettings


def _load_llm_settings() -> LLMSettings:
  default_path = Path(__file__).resolve().parents[2] / "config" / "llm.yaml"
  config_path = Path(os.getenv("NOVEL_TYPER_LLM_CONFIG", str(default_path))).resolve()
  payload = _read_yaml(config_path)

  request_payload = _dict(payload.get("request"))
  request_options = _deep_merge(
    _default_llm_request(),
    _common_request_options(request_payload),
  )
  non_stream_request_options = _deep_merge(
    request_options,
    _dict(request_payload.get(LLM_MODE_NON_STREAM)),
  )
  non_stream_request_options["stream"] = False

  headers = {
    **{"Accept": "application/json"},
    **{str(key): str(value) for key, value in _dict(payload.get("headers")).items()},
  }

  api_key_env = str(payload.get("api_key_env") or "DEEPSEEK_API_KEY")
  api_key = (
    os.getenv("NOVEL_TYPER_LLM_API_KEY")
    or os.getenv(api_key_env)
    or str(payload.get("api_key") or "")
  )

  base_url = (
    os.getenv("NOVEL_TYPER_LLM_BASE_URL")
    or str(payload.get("base_url") or "https://api.deepseek.com")
  )
  mode = LLM_MODE_NON_STREAM
  model = os.getenv("NOVEL_TYPER_LLM_MODEL") or str(
    payload.get("model") or "deepseek-v4-pro"
  )

  if "NOVEL_TYPER_LLM_TEMPERATURE" in os.environ:
    temperature = float(os.environ["NOVEL_TYPER_LLM_TEMPERATURE"])
    request_options["temperature"] = temperature
    non_stream_request_options["temperature"] = temperature
  if "NOVEL_TYPER_LLM_MAX_TOKENS" in os.environ:
    max_tokens = int(os.environ["NOVEL_TYPER_LLM_MAX_TOKENS"])
    request_options["max_tokens"] = max_tokens
    non_stream_request_options["max_tokens"] = max_tokens
  if "NOVEL_TYPER_LLM_TOP_P" in os.environ:
    top_p = float(os.environ["NOVEL_TYPER_LLM_TOP_P"])
    request_options["top_p"] = top_p
    non_stream_request_options["top_p"] = top_p
  if "NOVEL_TYPER_LLM_TOP_K" in os.environ:
    top_k = int(os.environ["NOVEL_TYPER_LLM_TOP_K"])
    request_options["top_k"] = top_k
    non_stream_request_options["top_k"] = top_k

  return LLMSettings(
    enabled=_parse_bool(
      os.getenv("NOVEL_TYPER_LLM_ENABLED"),
      _as_bool(payload.get("enabled"), True),
    ),
    api_key=api_key,
    api_key_required=_parse_bool(
      os.getenv("NOVEL_TYPER_LLM_API_KEY_REQUIRED"),
      _as_bool(payload.get("api_key_required"), True),
    ),
    base_url=base_url,
    mode=mode,
    model=model,
    timeout_seconds=float(
      os.getenv("NOVEL_TYPER_LLM_TIMEOUT_SECONDS", payload.get("timeout_seconds") or 60)
    ),
    headers=headers,
    request_options=request_options,
    non_stream_request_options=non_stream_request_options,
    config_path=config_path,
  )
