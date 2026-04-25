from __future__ import annotations


class DomainError(Exception):
  """Base class for service-level errors."""


class EntityNotFoundError(DomainError):
  """Raised when a project, chapter, or document cannot be found."""


class EntityConflictError(DomainError):
  """Raised when creating an entity that already exists."""


class InvalidProjectPathError(DomainError):
  """Raised when a requested path escapes the project data root."""


class LLMResponseFormatError(DomainError):
  """Raised when an LLM response is empty, truncated, or not valid JSON for the request."""


class LLMContextWindowExceededError(DomainError):
  """Raised before an LLM request when the estimated context exceeds model capacity."""


class LLMNotConfiguredError(DomainError):
  """Raised before opening a model stream when no usable LLM configuration exists."""


class LLMRequestError(DomainError):
  """Raised when a configured LLM request fails before a usable response is returned."""
