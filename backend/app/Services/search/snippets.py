from __future__ import annotations


def plain_snippet(value: str, query: str, radius: int = 36) -> str:
  if not value:
    return ""
  lower_value = value.casefold()
  lower_query = query.casefold()
  index = lower_value.find(lower_query)
  if index < 0:
    for term in query.split():
      index = lower_value.find(term.casefold())
      if index >= 0:
        lower_query = term.casefold()
        break
  if index < 0:
    return ""
  match_length = len(lower_query)
  start = max(0, index - radius)
  end = min(len(value), index + match_length + radius)
  prefix = "..." if start else ""
  suffix = "..." if end < len(value) else ""
  return (
    f"{prefix}{value[start:index]}<mark>{value[index:index + match_length]}</mark>"
    f"{value[index + match_length:end]}{suffix}"
  )
