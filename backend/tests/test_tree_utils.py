import pytest

from app.Utils.errors import EntityNotFoundError
from app.Utils.tree import collect_subtree_rows


def test_collect_subtree_rows_returns_root_and_descendants() -> None:
  rows = [
    {"id": "root", "parent_id": None},
    {"id": "child-a", "parent_id": "root"},
    {"id": "child-b", "parent_id": "root"},
    {"id": "grandchild", "parent_id": "child-a"},
    {"id": "other", "parent_id": None},
  ]

  assert [row["id"] for row in collect_subtree_rows(rows, "root", AssertionError())] == [
    "root",
    "child-a",
    "child-b",
    "grandchild",
  ]


def test_collect_subtree_rows_raises_domain_error_for_missing_node() -> None:
  with pytest.raises(EntityNotFoundError):
    collect_subtree_rows(
      [{"id": "root", "parent_id": None}],
      "missing",
      EntityNotFoundError("missing"),
    )
