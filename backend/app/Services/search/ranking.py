from __future__ import annotations


def normalize_limit(limit: int) -> int:
  return max(1, min(limit, 100))


def fts_order_sql() -> str:
  return "score ASC, m.updated_at DESC"


def like_score_sql() -> str:
  return """
        CASE
          WHEN m.title = ? THEN 0
          WHEN m.title LIKE ? THEN 1
          WHEN m.path_text LIKE ? THEN 2
          ELSE 3
        END AS score
      """
