from __future__ import annotations

import re
import unicodedata
from uuid import uuid4


def slugify(value: str, fallback_prefix: str = "project") -> str:
  normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
  slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
  slug = re.sub(r"-{2,}", "-", slug)
  return slug or f"{fallback_prefix}-{uuid4().hex[:8]}"
