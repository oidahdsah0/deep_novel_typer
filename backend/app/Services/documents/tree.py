from __future__ import annotations

from app.Schemas.documents import DocumentNode


def build_document_tree(rows: list[dict[str, object]]) -> list[DocumentNode]:
  nodes = {
    str(row["id"]): DocumentNode(
      id=str(row["id"]),
      parent_id=row["parent_id"],  # type: ignore[arg-type]
      type=row["type"],  # type: ignore[arg-type]
      title=str(row["title"]),
      updated_at=str(row["updated_at"]),
    )
    for row in rows
  }
  roots: list[DocumentNode] = []
  for row in rows:
    node = nodes[str(row["id"])]
    parent_id = row["parent_id"]
    if parent_id and str(parent_id) in nodes:
      nodes[str(parent_id)].children.append(node)
    else:
      roots.append(node)
  return roots
