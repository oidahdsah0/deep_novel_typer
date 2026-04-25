from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


LLM_MODE_NON_STREAM = "non_stream"


@dataclass(frozen=True)
class LLMSettings:
  enabled: bool
  api_key: str
  api_key_required: bool
  base_url: str
  mode: str
  model: str
  timeout_seconds: float
  headers: dict[str, str]
  request_options: dict[str, Any]
  non_stream_request_options: dict[str, Any]
  config_path: Path


@dataclass(frozen=True)
class GenerationPresetDefault:
  kind: str
  preset_id: str
  name: str
  content: str


@dataclass(frozen=True)
class GenerationSettings:
  presets: tuple[GenerationPresetDefault, ...]
  config_path: Path


@dataclass(frozen=True)
class Settings:
  app_name: str
  data_dir: Path
  db_path: Path
  trash_dir: Path
  cors_origins: list[str]
  cors_methods: list[str]
  cors_headers: list[str]
  thread_pool_workers: int
  llm: LLMSettings
  generation: GenerationSettings
