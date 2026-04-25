from __future__ import annotations

import re
from dataclasses import dataclass

import jieba

from app.Schemas.common import EmbeddingSegmentationMode
from app.Services.embeddings.cache import normalize_embedding_text

_TOKEN_CHARS = re.compile(r"[0-9A-Za-z\u4e00-\u9fff]")
_SENTENCE_ENDINGS = set("。！？!?；;")


@dataclass(frozen=True)
class TextSegment:
  token_index: int
  text: str
  normalized_text: str
  start_offset: int
  end_offset: int
  segmentation_mode: EmbeddingSegmentationMode


def segment_text(
  text: str,
  segmentation_mode: EmbeddingSegmentationMode,
  segment_size: int = 1,
) -> list[TextSegment]:
  if segmentation_mode == "word":
    return _group_segments(text, _segment_words(text), segment_size)
  if segmentation_mode == "sentence":
    return _group_segments(text, _segment_sentences(text), segment_size)
  raise ValueError(f"Unsupported segmentation mode: {segmentation_mode}")


def _segment_words(text: str) -> list[TextSegment]:
  segments: list[TextSegment] = []
  for word, start, end in jieba.tokenize(text, mode="default"):
    normalized = normalize_embedding_text(word)
    if not normalized or _TOKEN_CHARS.search(normalized) is None:
      continue
    segments.append(
      TextSegment(
        token_index=len(segments),
        text=word,
        normalized_text=normalized,
        start_offset=start,
        end_offset=end,
        segmentation_mode="word",
      )
    )
  return segments


def _segment_sentences(text: str) -> list[TextSegment]:
  segments: list[TextSegment] = []
  start: int | None = None
  for index, char in enumerate(text):
    if start is None and not char.isspace():
      start = index
    if start is None:
      continue
    if char in _SENTENCE_ENDINGS or char == "\n":
      _append_sentence_segment(segments, text, start, index + 1)
      start = None
  if start is not None:
    _append_sentence_segment(segments, text, start, len(text))
  return segments


def _append_sentence_segment(
  segments: list[TextSegment], text: str, start: int, end: int
) -> None:
  while start < end and text[start].isspace():
    start += 1
  while end > start and text[end - 1].isspace():
    end -= 1
  if start >= end:
    return
  segment_text_value = text[start:end]
  normalized = normalize_embedding_text(segment_text_value)
  if not normalized:
    return
  segments.append(
    TextSegment(
      token_index=len(segments),
      text=segment_text_value,
      normalized_text=normalized,
      start_offset=start,
      end_offset=end,
      segmentation_mode="sentence",
    )
  )


def _group_segments(
  text: str,
  segments: list[TextSegment],
  segment_size: int,
) -> list[TextSegment]:
  if segment_size <= 1:
    return segments

  grouped: list[TextSegment] = []
  for index in range(0, len(segments), segment_size):
    chunk = segments[index : index + segment_size]
    start = chunk[0].start_offset
    end = chunk[-1].end_offset
    value = text[start:end]
    normalized = normalize_embedding_text(value)
    if not normalized:
      continue
    grouped.append(
      TextSegment(
        token_index=len(grouped),
        text=value,
        normalized_text=normalized,
        start_offset=start,
        end_offset=end,
        segmentation_mode=chunk[0].segmentation_mode,
      )
    )
  return grouped
