from __future__ import annotations

from dataclasses import dataclass

from app.Schemas.prompt_context import PromptContextMaterialBlock
from app.Schemas.prompt_preview import PromptPreviewMaterial
from app.Schemas.prompt_profiles import PromptProfile
from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.prompt_profiles.context_formatting import material_block, render_material_blocks
from app.Services.prompt_profiles.rendering import clean_id_list, truncate
from app.Utils.errors import EntityConflictError, EntityNotFoundError


DEFAULT_MAX_ITEM_CHARS = 20000
DEFAULT_MAX_MATERIAL_CHARS = 120000
RECENT_CHAPTER_ENABLED_KEY = "recent_chapter_enabled"
RECENT_CHAPTER_COUNT_KEY = "recent_chapter_count"
DEFAULT_RECENT_CHAPTER_ENABLED = True
DEFAULT_RECENT_CHAPTER_COUNT = 2
MAX_RECENT_CHAPTER_COUNT = 20


@dataclass(frozen=True)
class ChapterReference:
  id: str
  source: str


@dataclass(frozen=True)
class RenderedPromptMaterials:
  text: str
  preview: list[PromptPreviewMaterial]
  blocks: list[PromptContextMaterialBlock]


class PromptMaterialRenderer:
  def __init__(
    self,
    chapter_service: ChapterService,
    document_service: DocumentService,
  ) -> None:
    self._chapter_service = chapter_service
    self._document_service = document_service

  async def resolve_chapter_refs(
    self,
    project_id: str,
    profile: PromptProfile,
    runtime_input: dict[str, object],
  ) -> list[ChapterReference]:
    fixed_ids = clean_id_list(profile.chapter_ids)
    recent_enabled, recent_count = recent_chapter_settings(profile.config)
    current_chapter_id = runtime_chapter_id(runtime_input)
    if not recent_enabled or recent_count <= 0 or not current_chapter_id:
      return [ChapterReference(id=chapter_id, source="fixed") for chapter_id in fixed_ids]

    recent_ids = await self.recent_chapter_ids(project_id, current_chapter_id, recent_count)
    return merge_chapter_refs(
      [
        *[ChapterReference(id=chapter_id, source="recent") for chapter_id in recent_ids],
        *[ChapterReference(id=chapter_id, source="fixed") for chapter_id in fixed_ids],
      ]
    )

  async def recent_chapter_ids(
    self, project_id: str, current_chapter_id: str, count: int
  ) -> list[str]:
    chapters = await self._chapter_service.list_chapters(project_id)
    current_index = next(
      (index for index, chapter in enumerate(chapters) if chapter.id == current_chapter_id),
      -1,
    )
    if current_index <= 0:
      return []
    start_index = max(0, current_index - count)
    return [chapter.id for chapter in chapters[start_index:current_index]]

  async def render_chapters(
    self,
    project_id: str,
    chapter_refs: list[ChapterReference],
    *,
    max_item_chars: int,
    max_total_chars: int,
  ) -> RenderedPromptMaterials:
    blocks: list[PromptContextMaterialBlock] = []
    for chapter_ref in chapter_refs:
      try:
        chapter = await self._chapter_service.get_chapter(project_id, chapter_ref.id)
      except EntityNotFoundError:
        continue
      truncated = len(chapter.content) > max_item_chars
      content = truncate(chapter.content, max_item_chars)
      block = material_block(
        id=chapter.id,
        title=chapter.title,
        kind="chapter",
        source=chapter_ref.source,
        content=content,
        format="plain",
        chars=len(chapter.content),
        truncated=truncated,
      )
      blocks.append(block)
    blocks = _fit_blocks_to_total(blocks, max_total_chars)
    materials = [_preview_material(block) for block in blocks]
    text = truncate(render_material_blocks(blocks), max_total_chars)
    return RenderedPromptMaterials(text=text, preview=materials, blocks=blocks)

  async def render_documents(
    self,
    project_id: str,
    document_ids: list[str],
    *,
    max_item_chars: int,
    max_total_chars: int,
  ) -> RenderedPromptMaterials:
    blocks: list[PromptContextMaterialBlock] = []
    for document_id in clean_id_list(document_ids):
      try:
        document = await self._document_service.get_document(project_id, document_id)
      except (EntityConflictError, EntityNotFoundError):
        continue
      truncated = len(document.content) > max_item_chars
      content = truncate(document.content, max_item_chars)
      block = material_block(
        id=document.id,
        title=document.title,
        kind="document",
        source="fixed",
        content=content,
        format="markdown",
        chars=len(document.content),
        truncated=truncated,
      )
      blocks.append(block)
    blocks = _fit_blocks_to_total(blocks, max_total_chars)
    materials = [_preview_material(block) for block in blocks]
    text = truncate(render_material_blocks(blocks), max_total_chars)
    return RenderedPromptMaterials(text=text, preview=materials, blocks=blocks)


def material_limits(config: dict[str, object]) -> tuple[int, int]:
  max_item_chars = config.get("max_item_chars")
  max_material_chars = config.get("max_material_chars")
  if not isinstance(max_item_chars, int):
    max_item_chars = DEFAULT_MAX_ITEM_CHARS
  if not isinstance(max_material_chars, int):
    max_material_chars = DEFAULT_MAX_MATERIAL_CHARS
  return (
    max(1000, min(max_item_chars, 200000)),
    max(2000, min(max_material_chars, 500000)),
  )


def recent_chapter_settings(config: dict[str, object]) -> tuple[bool, int]:
  enabled = config.get(RECENT_CHAPTER_ENABLED_KEY)
  if not isinstance(enabled, bool):
    enabled = DEFAULT_RECENT_CHAPTER_ENABLED
  count = bounded_int(
    config.get(RECENT_CHAPTER_COUNT_KEY),
    default=DEFAULT_RECENT_CHAPTER_COUNT,
    minimum=0,
    maximum=MAX_RECENT_CHAPTER_COUNT,
  )
  return enabled, count


def runtime_chapter_id(runtime_input: dict[str, object]) -> str:
  value = runtime_input.get("current_chapter_id") or runtime_input.get("chapter_id")
  return value.strip() if isinstance(value, str) else ""


def bounded_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
  if isinstance(value, bool):
    parsed = default
  elif isinstance(value, int):
    parsed = value
  elif isinstance(value, float) and value.is_integer():
    parsed = int(value)
  elif isinstance(value, str):
    try:
      parsed = int(value.strip())
    except ValueError:
      parsed = default
  else:
    parsed = default
  return max(minimum, min(parsed, maximum))


def default_config() -> dict[str, object]:
  return {
    RECENT_CHAPTER_ENABLED_KEY: DEFAULT_RECENT_CHAPTER_ENABLED,
    RECENT_CHAPTER_COUNT_KEY: DEFAULT_RECENT_CHAPTER_COUNT,
  }


def _fit_blocks_to_total(
  blocks: list[PromptContextMaterialBlock], max_total_chars: int
) -> list[PromptContextMaterialBlock]:
  result: list[PromptContextMaterialBlock] = []
  used = 0
  for block in blocks:
    if used >= max_total_chars:
      break
    remaining = max_total_chars - used
    content = block.content
    truncated = block.truncated
    if len(content) > remaining:
      content = truncate(content, remaining)
      truncated = True
    result.append(
      material_block(
        id=block.id,
        title=block.title,
        kind=block.kind,
        source=block.source,
        content=content,
        format=block.format,
        chars=block.chars,
        truncated=truncated,
      )
    )
    used += len(content)
  return result


def _preview_material(block: PromptContextMaterialBlock) -> PromptPreviewMaterial:
  return PromptPreviewMaterial(
    id=block.id,
    title=block.title,
    source=block.source,
    chars=block.chars,
    truncated=block.truncated,
    kind=block.kind,
    format=block.format,
    content_mode=block.content_mode,
    token_estimate=block.token_estimate,
  )


def merge_chapter_refs(chapter_refs: list[ChapterReference]) -> list[ChapterReference]:
  result: list[ChapterReference] = []
  index_by_id: dict[str, int] = {}
  for ref in chapter_refs:
    if not ref.id or len(ref.id) > 160:
      continue
    if ref.id in index_by_id:
      index = index_by_id[ref.id]
      existing = result[index]
      if ref.source not in existing.source.split("+"):
        result[index] = ChapterReference(
          id=existing.id,
          source=f"{existing.source}+{ref.source}",
        )
      continue
    index_by_id[ref.id] = len(result)
    result.append(ref)
  return result[:500]
