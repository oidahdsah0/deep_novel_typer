from __future__ import annotations

import asyncio
import logging
from hashlib import sha1

from app.Services.api_configs import APIConfigService, EffectiveAPIConfig, build_llm_overrides
from app.Services.chapter_service import ChapterService
from app.Services.context_limits import SUGGESTION_CONTEXT_CHARS
from app.Services.debug_log_service import DebugLogService, LLMDebugContext
from app.Services.prompt_builder import parse_suggestion_payload
from app.Services.prompt_profiles import PromptProfileService
from app.Services.structured_outputs import StructuredOutputContext
from app.Services.structured_llm_service import complete_json
from app.Services.perspective_service import PerspectiveService
from app.Services.project_service import ProjectService
from app.Utils.errors import (
  EntityNotFoundError,
  LLMContextWindowExceededError,
  LLMResponseFormatError,
)
from app.Utils.llm import CompletionClient, LLMRequestOverrides
from app.Schemas.perspectives import Perspective
from app.Schemas.suggestions import SuggestionCard, SuggestionSeverity
from app.Utils.text import count_words, tail_text


_LOGGER = logging.getLogger(__name__)


class SuggestionService:
  def __init__(
    self,
    chapter_service: ChapterService,
    perspective_service: PerspectiveService,
    project_service: ProjectService,
    prompt_profile_service: PromptProfileService,
    api_config_service: APIConfigService,
    llm_client: CompletionClient,
    debug_log_service: DebugLogService | None = None,
  ) -> None:
    self._chapter_service = chapter_service
    self._perspective_service = perspective_service
    self._project_service = project_service
    self._prompt_profile_service = prompt_profile_service
    self._api_config_service = api_config_service
    self._llm_client = llm_client
    self._debug_log_service = debug_log_service

  async def suggest_for_paragraph(
    self,
    project_id: str,
    chapter_id: str,
    paragraph: str,
    perspective_id: str | None = None,
  ) -> list[SuggestionCard]:
    perspective_ids = (
      [perspective_id]
      if perspective_id
      else await self.list_enabled_perspective_ids(project_id)
    )
    if not perspective_ids:
      return []

    suggestion_groups = await asyncio.gather(
      *[
        self.suggest_for_perspective(project_id, chapter_id, paragraph, item)
        for item in perspective_ids
      ],
      return_exceptions=True,
    )
    exceptions: list[BaseException] = []
    for perspective, group in zip(perspective_ids, suggestion_groups, strict=True):
      if isinstance(group, LLMContextWindowExceededError):
        raise group
      if isinstance(group, BaseException):
        exceptions.append(group)
        _LOGGER.warning(
          "Suggestion request failed for perspective %s in project %s chapter %s: %s",
          perspective,
          project_id,
          chapter_id,
          group,
        )
    if exceptions and len(exceptions) == len(suggestion_groups):
      raise exceptions[0]
    return [
      suggestion
      for group in suggestion_groups
      if not isinstance(group, BaseException)
      for suggestion in group
    ]

  async def list_enabled_perspective_ids(self, project_id: str) -> list[str]:
    return [
      item.id
      for item in await self._perspective_service.list_perspectives(project_id)
      if item.is_enabled
    ]

  async def suggest_for_perspective(
    self,
    project_id: str,
    chapter_id: str,
    paragraph: str,
    perspective_id: str,
  ) -> list[SuggestionCard]:
    chapter = await self._chapter_service.get_chapter(project_id, chapter_id)
    perspective = next(
      (
        item
        for item in await self._perspective_service.list_perspectives(project_id)
        if item.id == perspective_id
      ),
      None,
    )
    if perspective is None:
      return []

    normalized_paragraph = paragraph.strip()
    if not normalized_paragraph:
      return []

    return await self._suggest_for_single_perspective(
      project_id=project_id,
      chapter_id=chapter_id,
      chapter_title=chapter.title,
      chapter_content=chapter.content,
      paragraph=normalized_paragraph,
      perspective=perspective,
    )

  async def suggest_locally_for_paragraph(
    self, project_id: str, chapter_id: str, paragraph: str
  ) -> list[SuggestionCard]:
    perspectives = [
      item
      for item in await self._perspective_service.list_perspectives(project_id)
      if item.is_enabled
    ]
    if not perspectives:
      return []
    return _build_local_suggestions(project_id, chapter_id, paragraph.strip(), perspectives)

  async def _suggest_for_single_perspective(
    self,
    *,
    project_id: str,
    chapter_id: str,
    chapter_title: str,
    chapter_content: str,
    paragraph: str,
    perspective: Perspective,
  ) -> list[SuggestionCard]:
    try:
      config_id = (
        perspective.api_config_id
        or await self._prompt_profile_service.request_api_config_id(
          project_id,
          "perspective_suggestion",
        )
      )
      effective_config = await self._api_config_service.get_effective_config(
        config_id,
        kind="llm",
      )
    except EntityNotFoundError:
      effective_config = None

    if effective_config is not None:
      llm_overrides = build_llm_overrides(
        effective_config,
        temperature_override=await self._prompt_profile_service.request_temperature(
          project_id,
          "perspective_suggestion",
        ),
      )
      if self._llm_client.is_configured_for(llm_overrides):
        cards = await self._suggest_with_llm(
          project_id=project_id,
          chapter_id=chapter_id,
          chapter_title=chapter_title,
          chapter_content=chapter_content,
          paragraph=paragraph,
          perspectives=[perspective],
          effective_config=effective_config,
          llm_overrides=llm_overrides,
        )
        if cards:
          return cards

    return _build_local_suggestions(project_id, chapter_id, paragraph, [perspective])

  async def _suggest_with_llm(
    self,
    *,
    project_id: str,
    chapter_id: str,
    chapter_title: str,
    chapter_content: str,
    paragraph: str,
    perspectives: list[Perspective],
    effective_config: EffectiveAPIConfig,
    llm_overrides: LLMRequestOverrides,
  ) -> list[SuggestionCard]:
    try:
      project = await self._project_service.get_manifest(project_id)
      prompt_build = await self._prompt_profile_service.build_preview(
        project_id,
        "perspective_suggestion",
        {
          "project": {
            "title": project.title,
            "subtitle": project.subtitle,
            "genre": project.genre,
            "status": project.status,
            "description": project.description,
          },
          "current_chapter_id": chapter_id,
          "chapter_title": chapter_title,
          "current_chapter": tail_text(chapter_content, SUGGESTION_CONTEXT_CHARS, strip=True),
          "current_paragraph": paragraph,
          "perspectives": [
            {
              "id": perspective.id,
              "name": perspective.name,
              "description": perspective.description,
              "instructions": perspective.instructions,
            }
            for perspective in perspectives
          ],
        },
      )
      response = await complete_json(
        self._llm_client,
        "perspective_suggestion",
        prompt_build.messages,
        llm_overrides,
        self._debug_log_service,
        _debug_context(project_id, "perspective_suggestion", effective_config),
        validation_context=StructuredOutputContext(
          valid_perspective_ids=frozenset(perspective.id for perspective in perspectives)
        ),
        context_pack=prompt_build.context_pack,
        context_window_tokens=effective_config.config.context_window_tokens,
      )
      drafts = parse_suggestion_payload(
        response.payload, {perspective.id for perspective in perspectives}
      )
    except LLMContextWindowExceededError:
      raise
    except LLMResponseFormatError:
      return []

    perspective_names = {perspective.id: perspective.name for perspective in perspectives}
    return [
      SuggestionCard(
        id=_suggestion_id(project_id, perspective_id=draft.perspective_id, paragraph=paragraph),
        perspective_id=draft.perspective_id,
        perspective_name=perspective_names[draft.perspective_id],
        title=draft.title,
        body=draft.body,
        detail=draft.detail,
        severity=draft.severity,
        source="llm",
        model=response.model,
      )
      for draft in drafts
    ]


def _build_local_suggestions(
  project_id: str, chapter_id: str, paragraph: str, perspectives: list[Perspective]
) -> list[SuggestionCard]:
  paragraph_word_count = count_words(paragraph)
  suggestions: list[SuggestionCard] = []
  for perspective in perspectives:
    title, body, severity = _build_suggestion(perspective.id, paragraph_word_count)
    detail = _build_suggestion_detail(perspective.id, paragraph_word_count)
    suggestions.append(
      SuggestionCard(
        id=_suggestion_id(
          project_id,
          chapter_id=chapter_id,
          perspective_id=perspective.id,
          paragraph=paragraph,
        ),
        perspective_id=perspective.id,
        perspective_name=perspective.name,
        title=title,
        body=body,
        detail=detail,
        severity=severity,
        source="local",
      )
    )

  return suggestions


def _debug_context(
  project_id: str, request_type: str, effective_config: EffectiveAPIConfig
) -> LLMDebugContext:
  settings = effective_config.config
  return LLMDebugContext(
    project_id=project_id,
    request_type=request_type,
    api_config_id=settings.id,
    provider=settings.provider,
    model=settings.model,
  )


def _build_suggestion(
  perspective_id: str, paragraph_word_count: int
) -> tuple[str, str, SuggestionSeverity]:
  if perspective_id == "pace-editor":
    if paragraph_word_count > 220:
      return (
        "段落信息偏密",
        "这一段承载的信息较多，可以拆成两个节拍：先保留动作，再让关键信息单独落地。",
        SuggestionSeverity.focus,
      )
    return (
      "推进节奏清爽",
      "当前段落长度利于阅读，可以补一个更具象的动作或道具，让悬念更容易被记住。",
      SuggestionSeverity.calm,
    )

  if perspective_id == "character-critic":
    return (
      "人物反应可具身化",
      "建议把心理判断落到动作、停顿或微表情上，让读者通过行为理解人物状态。",
      SuggestionSeverity.focus,
    )

  return (
    "检查设定锚点",
    "留意时间、地点、称呼和道具是否会在后续章节复用；必要时同步到大纲或伏笔清单。",
    SuggestionSeverity.risk,
  )


def _build_suggestion_detail(perspective_id: str, paragraph_word_count: int) -> str:
  if perspective_id == "pace-editor":
    if paragraph_word_count > 220:
      return (
        "当前段落的阅读负载偏高，读者需要同时处理动作、信息和悬念。"
        "可以把最重要的信息单独放到下一句或下一段，让节奏有一次清晰落点。"
        "如果这是高潮段，也可以保留密度，但建议补一个短动作作为换气点。"
      )
    return (
      "当前段落没有明显拖沓，适合继续推进。"
      "轻量增强方向是给悬念或目标加一个更可见的动作锚点，让读者更容易记住这一拍。"
    )

  if perspective_id == "character-critic":
    return (
      "人物情绪如果只停留在判断句里，会削弱画面感。"
      "可以挑一个心理变化，落到手势、停顿、视线或语气上。"
      "不需要重写整段，只要加一个能暴露人物状态的小动作即可。"
    )

  return (
    "这类细节最容易在后文变成连续性约束。"
    "如果当前段落引入了称呼、地点、时间、规则或道具，建议确认它是否需要进入资料或伏笔清单。"
    "没有明显冲突时，也可以只记录一个轻量提醒，避免后续遗忘。"
  )


def _suggestion_id(
  project_id: str,
  *,
  perspective_id: str,
  paragraph: str,
  chapter_id: str = "",
) -> str:
  value = f"{project_id}:{chapter_id}:{perspective_id}:{paragraph}"
  return sha1(value.encode()).hexdigest()[:10]
