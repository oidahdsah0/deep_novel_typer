from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
  from app.Services.documents.service import DocumentService

__all__ = ["DocumentService"]


def __getattr__(name: str):
  if name == "DocumentService":
    # Keep package imports light for tooling that only needs document helpers.
    from app.Services.documents.service import DocumentService

    return DocumentService
  raise AttributeError(name)
