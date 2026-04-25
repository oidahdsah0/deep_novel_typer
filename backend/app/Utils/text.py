from __future__ import annotations

import re

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_LATIN_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")


def count_words(text: str) -> int:
  cjk_count = len(_CJK_RE.findall(text))
  latin_count = len(_LATIN_WORD_RE.findall(_CJK_RE.sub(" ", text)))
  return cjk_count + latin_count


def extract_last_paragraph(text: str) -> str:
  paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
  return paragraphs[-1] if paragraphs else ""


def tail_text(text: str, limit: int, *, strip: bool = False) -> str:
  value = text.strip() if strip else text
  if len(value) <= limit:
    return value
  return value[-limit:]
