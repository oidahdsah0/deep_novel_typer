from __future__ import annotations

from app.Schemas.prompt_context import PromptContextFocusBlock
from app.Services.prompt_profiles.context_formatting import focus_block


def chapter_synopsis_blocks(
  runtime_input: dict[str, object], *, optional: bool = False
) -> list[PromptContextFocusBlock]:
  if "chapter_synopsis" not in runtime_input:
    return []
  metadata = {"optional": True} if optional else None
  return [
    focus_block(
      key="chapter_synopsis",
      label="本章写作梗概",
      content=_text(runtime_input.get("chapter_synopsis")),
      format="markdown",
      metadata=metadata,
    )
  ]


def document_chapter_context_blocks(
  runtime_input: dict[str, object],
) -> list[PromptContextFocusBlock]:
  blocks: list[PromptContextFocusBlock] = []
  if _text(runtime_input.get("chapter_title")):
    blocks.append(
      focus_block(
        key="chapter_title",
        label="关联章节标题",
        content=_text(runtime_input.get("chapter_title")),
        metadata={"optional": True},
      )
    )
  blocks.extend(chapter_synopsis_blocks(runtime_input, optional=True))
  return blocks


def _text(value: object) -> str:
  if value is None:
    return ""
  if isinstance(value, str):
    return value
  return str(value)
