from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from app.Utils.config_generation import _load_generation_settings
from app.Utils.config_helpers import _split_csv
from app.Utils.config_llm import _load_llm_settings
from app.Utils.config_types import Settings


@lru_cache
def get_settings() -> Settings:
  default_backend_data_dir = Path(__file__).resolve().parents[2] / "data"
  default_projects_dir = default_backend_data_dir / "projects"
  cors_origins = os.getenv(
    "NOVEL_TYPER_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
  )

  return Settings(
    app_name=os.getenv("NOVEL_TYPER_APP_NAME", "Deep Novel Typer API"),
    data_dir=Path(os.getenv("NOVEL_TYPER_DATA_DIR", str(default_projects_dir))).resolve(),
    db_path=Path(
      os.getenv("NOVEL_TYPER_DB_PATH", str(default_backend_data_dir / "novel.db"))
    ).resolve(),
    trash_dir=Path(
      os.getenv("NOVEL_TYPER_TRASH_DIR", str(default_backend_data_dir / "trash"))
    ).resolve(),
    cors_origins=_split_csv(cors_origins),
    cors_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    cors_headers=["Authorization", "Content-Type", "Accept"],
    thread_pool_workers=int(os.getenv("NOVEL_TYPER_THREAD_POOL_WORKERS", "8")),
    llm=_load_llm_settings(),
    generation=_load_generation_settings(),
  )
