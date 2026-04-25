from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any

from app.Utils.errors import DomainError, InvalidProjectPathError

MAX_ARCHIVE_BYTES = 200 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 20000
MAX_ENTRY_BYTES = 50 * 1024 * 1024
CONTENT_PREFIX = "content/"


@dataclass
class ProjectArchivePayload:
  manifest: dict[str, Any]
  data: dict[str, Any]
  content_files: dict[str, bytes]
  checksums: dict[str, str] = field(default_factory=dict)


class ProjectArchiveBuilder:
  def __init__(self) -> None:
    self._json_files: dict[str, Any] = {}
    self._content_files: dict[str, str] = {}
    self._checksums: dict[str, str] = {}

  def add_json(self, path: str, payload: Any) -> None:
    _assert_archive_path(path)
    self._json_files[path] = payload

  def add_content_text(self, relative_path: str, content: str) -> None:
    clean_path = safe_relative_path(relative_path)
    archive_path = f"{CONTENT_PREFIX}{clean_path}"
    _assert_archive_path(archive_path)
    self._content_files[archive_path] = content
    self._checksums[clean_path] = sha256(content.encode("utf-8")).hexdigest()

  def build(self) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
      for path, payload in self._json_files.items():
        archive.writestr(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
      archive.writestr(
        "checksums.json",
        json.dumps(self._checksums, ensure_ascii=False, indent=2) + "\n",
      )
      for path, content in self._content_files.items():
        archive.writestr(path, content)
    return buffer.getvalue()


def read_project_archive(raw: bytes) -> ProjectArchivePayload:
  if len(raw) > MAX_ARCHIVE_BYTES:
    raise DomainError("Project import archive is too large")
  try:
    zip_buffer = BytesIO(raw)
    with zipfile.ZipFile(zip_buffer, "r") as archive:
      members = archive.infolist()
      if len(members) > MAX_ARCHIVE_ENTRIES:
        raise DomainError("Project import archive contains too many files")
      for member in members:
        _assert_archive_path(member.filename)
        if member.file_size > MAX_ENTRY_BYTES:
          raise DomainError(f"Project import archive entry is too large: {member.filename}")

      manifest = _read_json_member(archive, "manifest.json")
      checksums = _read_json_member(archive, "checksums.json", required=False) or {}
      data: dict[str, Any] = {}
      content_files: dict[str, bytes] = {}
      for member in members:
        name = member.filename
        if name.startswith("data/") and name.endswith(".json"):
          data[name.removeprefix("data/").removesuffix(".json")] = _read_json_member(
            archive, name
          )
        elif name.startswith(CONTENT_PREFIX) and not name.endswith("/"):
          relative_path = safe_relative_path(name.removeprefix(CONTENT_PREFIX))
          content_files[relative_path] = archive.read(name)

      _verify_checksums(checksums, content_files)
      return ProjectArchivePayload(
        manifest=manifest,
        data=data,
        content_files=content_files,
        checksums=checksums,
      )
  except zipfile.BadZipFile as exc:
    raise DomainError("Project import archive is not a valid zip file") from exc


def safe_relative_path(value: object) -> str:
  raw = str(value or "").replace("\\", "/").strip()
  if not raw:
    raise InvalidProjectPathError("Empty archive path")
  path = PurePosixPath(raw)
  if path.is_absolute() or ".." in path.parts:
    raise InvalidProjectPathError(f"Archive path escapes project root: {raw}")
  return path.as_posix()


def _assert_archive_path(path: str) -> None:
  normalized = path.replace("\\", "/")
  posix_path = PurePosixPath(normalized)
  if posix_path.is_absolute() or ".." in posix_path.parts:
    raise InvalidProjectPathError(f"Archive path escapes zip root: {path}")


def _read_json_member(
  archive: zipfile.ZipFile, name: str, *, required: bool = True
) -> dict[str, Any] | None:
  try:
    raw = archive.read(name)
  except KeyError:
    if required:
      raise DomainError(f"Project import archive is missing {name}") from None
    return None
  try:
    payload = json.loads(raw.decode("utf-8"))
  except (UnicodeDecodeError, json.JSONDecodeError) as exc:
    raise DomainError(f"Project import archive contains invalid JSON: {name}") from exc
  if not isinstance(payload, dict):
    raise DomainError(f"Project import archive JSON must be an object: {name}")
  return payload


def _verify_checksums(checksums: object, content_files: dict[str, bytes]) -> None:
  if not isinstance(checksums, dict):
    raise DomainError("Project import archive checksums must be an object")
  for path, expected in checksums.items():
    relative_path = safe_relative_path(path)
    content = content_files.get(relative_path)
    if content is None:
      raise DomainError(f"Project import archive is missing content file: {relative_path}")
    actual = sha256(content).hexdigest()
    if actual != expected:
      raise DomainError(f"Project import archive checksum mismatch: {relative_path}")
