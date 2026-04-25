from __future__ import annotations

from collections import deque


def collect_subtree_rows(
  rows: list[dict[str, object]],
  node_id: str,
  not_found_error: Exception,
  *,
  id_key: str = "id",
  parent_key: str = "parent_id",
) -> list[dict[str, object]]:
  nodes = {str(row[id_key]): row for row in rows}
  if node_id not in nodes:
    raise not_found_error

  children: dict[str | None, list[dict[str, object]]] = {}
  for row in rows:
    parent_id = row[parent_key]
    children.setdefault(str(parent_id) if parent_id else None, []).append(row)

  collected: list[dict[str, object]] = []
  queue: deque[str] = deque([node_id])
  while queue:
    current_id = queue.popleft()
    row = nodes[current_id]
    collected.append(row)
    for child in children.get(current_id, []):
      queue.append(str(child[id_key]))
  return collected
