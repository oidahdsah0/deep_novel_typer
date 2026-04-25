from __future__ import annotations

from app.Schemas.search import ProjectSearchResourceType, ProjectSearchScope


SCOPE_TYPES: dict[ProjectSearchScope, tuple[ProjectSearchResourceType, ...]] = {
  "all": (
    "chapter",
    "document",
    "prompt_profile",
    "prompt_profile_version",
    "generation_preset",
    "resource_version",
  ),
  "chapters": ("chapter",),
  "documents": ("document",),
  "prompts": ("prompt_profile", "prompt_profile_version"),
  "presets": ("generation_preset",),
  "versions": ("prompt_profile_version", "resource_version"),
}


def normalize_query(query: str) -> str:
  return " ".join(query.strip().split())


def resource_types_for_scope(
  scope: ProjectSearchScope,
) -> tuple[ProjectSearchResourceType, ...]:
  return SCOPE_TYPES[scope]


def should_use_like_search(query: str) -> bool:
  terms = query.split()
  return any(len(term) < 3 for term in terms) or len(query) < 3


def fts_query(query: str) -> str:
  terms = [term.replace('"', '""') for term in query.split() if term]
  return " AND ".join(f'"{term}"' for term in terms) or '""'
