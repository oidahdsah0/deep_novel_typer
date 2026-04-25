from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.Utils.errors import InvalidProjectPathError


@dataclass(frozen=True)
class ProjectPaths:
  root: Path
  manifest: Path
  chapters_dir: Path
  docs_dir: Path
  perspectives_dir: Path
  versions_dir: Path


class PathResolver:
  def __init__(self, data_dir: Path, trash_dir: Path | None = None) -> None:
    self.data_dir = data_dir.resolve()
    self.trash_dir = (trash_dir or data_dir.parent / "trash").resolve()

  def project(self, project_id: str) -> ProjectPaths:
    root = self._inside_root(self.data_dir / project_id)
    return ProjectPaths(
      root=root,
      manifest=root / "manifest.json",
      chapters_dir=root / "chapters",
      docs_dir=root / "docs",
      perspectives_dir=root / "perspectives",
      versions_dir=root / "versions",
    )

  def trashed_project(self, project_id: str, suffix: str) -> Path:
    return self._inside_trash(self.trash_dir / f"{project_id}-{suffix}")

  def trashed_project_item(
    self,
    project_id: str,
    category: str,
    item_id: str,
    suffix: str,
  ) -> Path:
    return self._inside_trash(self.trash_dir / project_id / category / f"{item_id}-{suffix}")

  def _inside_root(self, path: Path) -> Path:
    resolved = path.resolve()
    if resolved != self.data_dir and self.data_dir not in resolved.parents:
      raise InvalidProjectPathError(f"Path escapes project data root: {resolved}")
    return resolved

  def _inside_trash(self, path: Path) -> Path:
    resolved = path.resolve()
    if resolved != self.trash_dir and self.trash_dir not in resolved.parents:
      raise InvalidProjectPathError(f"Path escapes trash data root: {resolved}")
    return resolved
