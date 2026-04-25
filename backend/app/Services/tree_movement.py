from __future__ import annotations

from dataclasses import dataclass

from app.Utils.errors import EntityConflictError, EntityNotFoundError


@dataclass(frozen=True)
class TreeNodeMoveUpdate:
  node_id: str
  parent_id: str | None
  order_index: int


def plan_tree_move(
  rows: list[dict[str, object]],
  *,
  node_id: str,
  parent_id: str | None,
  before_node_id: str | None,
  not_found_label: str,
) -> list[TreeNodeMoveUpdate]:
  nodes = {str(row["id"]): row for row in rows}
  if node_id not in nodes:
    raise EntityNotFoundError(f"{not_found_label} not found: {node_id}")
  if parent_id is not None:
    parent = nodes.get(parent_id)
    if parent is None:
      raise EntityNotFoundError(f"{not_found_label} parent not found: {parent_id}")
    if str(parent["type"]) != "folder":
      raise EntityConflictError("Target parent must be a folder")
  if before_node_id == node_id:
    if parent_id == _parent_key(nodes[node_id]):
      return []
    raise EntityConflictError("before_node_id cannot be the moving node")
  if before_node_id is not None:
    before_node = nodes.get(before_node_id)
    if before_node is None:
      raise EntityNotFoundError(f"{not_found_label} before node not found: {before_node_id}")
    if _parent_key(before_node) != parent_id:
      raise EntityConflictError("before_node_id must belong to the target parent")
    if before_node_id in _descendant_ids(rows, node_id):
      raise EntityConflictError("Cannot move a folder relative to one of its descendants")

  if parent_id == node_id or (parent_id is not None and parent_id in _descendant_ids(rows, node_id)):
    raise EntityConflictError("Cannot move a folder into one of its descendants")

  original_parent_id = _parent_key(nodes[node_id])
  if parent_id == original_parent_id:
    target_siblings = [
      row for row in _siblings(rows, parent_id)
      if str(row["id"]) != node_id
    ]
    next_siblings = _insert_before(target_siblings, nodes[node_id], before_node_id)
    return _updates_for_siblings(next_siblings, parent_id)

  old_siblings = [
    row for row in _siblings(rows, original_parent_id)
    if str(row["id"]) != node_id
  ]
  target_siblings = _siblings(rows, parent_id)
  next_target_siblings = _insert_before(target_siblings, nodes[node_id], before_node_id)
  return [
    *_updates_for_siblings(old_siblings, original_parent_id),
    *_updates_for_siblings(next_target_siblings, parent_id),
  ]


def rows_with_updates(
  rows: list[dict[str, object]], updates: list[TreeNodeMoveUpdate]
) -> list[dict[str, object]]:
  updates_by_id = {update.node_id: update for update in updates}
  next_rows: list[dict[str, object]] = []
  for row in rows:
    update = updates_by_id.get(str(row["id"]))
    if update is None:
      next_rows.append(row)
      continue
    next_rows.append({**row, "parent_id": update.parent_id, "order_index": update.order_index})
  return next_rows


def _siblings(rows: list[dict[str, object]], parent_id: str | None) -> list[dict[str, object]]:
  return [
    row for row in rows
    if _parent_key(row) == parent_id
  ]


def _insert_before(
  siblings: list[dict[str, object]],
  moving_node: dict[str, object],
  before_node_id: str | None,
) -> list[dict[str, object]]:
  if before_node_id is None:
    return [*siblings, moving_node]
  next_siblings: list[dict[str, object]] = []
  inserted = False
  for sibling in siblings:
    if str(sibling["id"]) == before_node_id:
      next_siblings.append(moving_node)
      inserted = True
    next_siblings.append(sibling)
  if not inserted:
    raise EntityConflictError("before_node_id must belong to the target parent")
  return next_siblings


def _updates_for_siblings(
  siblings: list[dict[str, object]], parent_id: str | None
) -> list[TreeNodeMoveUpdate]:
  return [
    TreeNodeMoveUpdate(
      node_id=str(row["id"]),
      parent_id=parent_id,
      order_index=index + 1,
    )
    for index, row in enumerate(siblings)
  ]


def _descendant_ids(rows: list[dict[str, object]], node_id: str) -> set[str]:
  children: dict[str | None, list[str]] = {}
  for row in rows:
    children.setdefault(_parent_key(row), []).append(str(row["id"]))
  descendants: set[str] = set()
  stack = list(children.get(node_id, []))
  while stack:
    child_id = stack.pop()
    descendants.add(child_id)
    stack.extend(children.get(child_id, []))
  return descendants


def _parent_key(row: dict[str, object]) -> str | None:
  parent_id = row["parent_id"]
  return str(parent_id) if parent_id else None
