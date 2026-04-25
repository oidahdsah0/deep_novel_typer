from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from app.Schemas.search import ProjectSearchResourceType


@dataclass(frozen=True)
class SearchDocument:
  project_id: str
  resource_type: ProjectSearchResourceType
  resource_id: str
  title: str
  body: str
  updated_at: str
  resource_subtype: str = ""
  path: list[str] = field(default_factory=list)
  metadata: dict[str, object] = field(default_factory=dict)

  @property
  def path_text(self) -> str:
    return " / ".join(item for item in self.path if item)

  @property
  def content_hash(self) -> str:
    payload = {
      "body": self.body,
      "metadata": self.metadata,
      "path": self.path,
      "resource_subtype": self.resource_subtype,
      "title": self.title,
    }
    return sha256(
      json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


async def upsert_search_document(conn: Any, document: SearchDocument) -> None:
  extra_json = json.dumps(document.metadata, ensure_ascii=False, sort_keys=True)
  cursor = await conn.execute(
    """
    SELECT rowid FROM project_search_meta
    WHERE project_id = ? AND resource_type = ? AND resource_id = ?
    """,
    (document.project_id, document.resource_type, document.resource_id),
  )
  row = await cursor.fetchone()
  await cursor.close()

  if row is None:
    cursor = await conn.execute(
      """
      INSERT INTO project_search_meta (
        project_id, resource_type, resource_id, resource_subtype,
        title, path_text, content_hash, updated_at, extra_json
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      """,
      (
        document.project_id,
        document.resource_type,
        document.resource_id,
        document.resource_subtype,
        document.title,
        document.path_text,
        document.content_hash,
        document.updated_at,
        extra_json,
      ),
    )
    rowid = cursor.lastrowid
    await cursor.close()
  else:
    rowid = row["rowid"]
    await conn.execute(
      """
      UPDATE project_search_meta
      SET resource_subtype = ?,
          title = ?,
          path_text = ?,
          content_hash = ?,
          updated_at = ?,
          extra_json = ?
      WHERE rowid = ?
      """,
      (
        document.resource_subtype,
        document.title,
        document.path_text,
        document.content_hash,
        document.updated_at,
        extra_json,
        rowid,
      ),
    )

  await conn.execute("DELETE FROM project_search_fts WHERE rowid = ?", (rowid,))
  await conn.execute(
    """
    INSERT INTO project_search_fts (
      rowid, project_id, resource_type, resource_id, resource_subtype, title, path_text, body
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
      rowid,
      document.project_id,
      document.resource_type,
      document.resource_id,
      document.resource_subtype,
      document.title,
      document.path_text,
      document.body,
    ),
  )


async def delete_search_document(
  conn: Any,
  project_id: str,
  resource_type: ProjectSearchResourceType,
  resource_id: str,
) -> None:
  cursor = await conn.execute(
    """
    SELECT rowid FROM project_search_meta
    WHERE project_id = ? AND resource_type = ? AND resource_id = ?
    """,
    (project_id, resource_type, resource_id),
  )
  rows = await cursor.fetchall()
  await cursor.close()
  for row in rows:
    await conn.execute("DELETE FROM project_search_fts WHERE rowid = ?", (row["rowid"],))
  await conn.execute(
    """
    DELETE FROM project_search_meta
    WHERE project_id = ? AND resource_type = ? AND resource_id = ?
    """,
    (project_id, resource_type, resource_id),
  )


async def delete_search_documents(
  conn: Any,
  project_id: str,
  resource_type: ProjectSearchResourceType,
  resource_ids: list[str],
) -> None:
  for resource_id in resource_ids:
    await delete_search_document(conn, project_id, resource_type, resource_id)


async def delete_project_search(conn: Any, project_id: str) -> None:
  cursor = await conn.execute(
    "SELECT rowid FROM project_search_meta WHERE project_id = ?",
    (project_id,),
  )
  rows = await cursor.fetchall()
  await cursor.close()
  for row in rows:
    await conn.execute("DELETE FROM project_search_fts WHERE rowid = ?", (row["rowid"],))
  await conn.execute("DELETE FROM project_search_meta WHERE project_id = ?", (project_id,))
