from __future__ import annotations

from app.Schemas.chapters import ChapterNode


def build_chapter_tree(rows: list[dict[str, object]]) -> list[ChapterNode]:
  nodes = {
    str(row["id"]): ChapterNode(
      id=str(row["id"]),
      parent_id=row["parent_id"],  # type: ignore[arg-type]
      type=row["type"],  # type: ignore[arg-type]
      title=str(row["title"]),
      chapter_id=row["chapter_id"],  # type: ignore[arg-type]
      word_count=int(row["word_count"] or 0),
      updated_at=str(row["updated_at"]),
    )
    for row in rows
  }
  roots: list[ChapterNode] = []
  for row in rows:
    node = nodes[str(row["id"])]
    parent_id = row["parent_id"]
    if parent_id and str(parent_id) in nodes:
      nodes[str(parent_id)].children.append(node)
    else:
      roots.append(node)
  return roots


def chapter_order_updates(rows: list[dict[str, object]]) -> list[tuple[str, int]]:
  children: dict[str | None, list[dict[str, object]]] = {}
  for row in rows:
    parent_id = row["parent_id"]
    children.setdefault(str(parent_id) if parent_id else None, []).append(row)

  for sibling_rows in children.values():
    sibling_rows.sort(key=lambda row: int(row["order_index"] or 0))

  updates: list[tuple[str, int]] = []

  def walk(parent_id: str | None) -> None:
    for row in children.get(parent_id, []):
      if row["chapter_id"]:
        updates.append((str(row["chapter_id"]), len(updates) + 1))
      if str(row["type"]) == "folder":
        walk(str(row["id"]))

  walk(None)
  return updates


def chapter_paths(rows: list[dict[str, object]]) -> dict[str, list[str]]:
  nodes = {str(row["id"]): row for row in rows}
  paths: dict[str, list[str]] = {}
  for node_id, row in nodes.items():
    if str(row["type"]) != "chapter":
      continue
    path: list[str] = []
    parent_id = row["parent_id"]
    while parent_id and str(parent_id) in nodes:
      parent = nodes[str(parent_id)]
      path.append(str(parent["title"]))
      parent_id = parent["parent_id"]
    paths[node_id] = list(reversed(path))
  return paths
