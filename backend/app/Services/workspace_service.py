from __future__ import annotations

from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.generation_service import GenerationService
from app.Services.perspective_service import PerspectiveService
from app.Services.prompt_profiles import PromptProfileService
from app.Services.project_service import ProjectService
from app.Services.suggestion_service import SuggestionService
from app.Services.typewriter_layout import TypewriterLayoutService
from app.Schemas.workspace import ActiveChapter, WorkspaceSnapshot


class WorkspaceService:
  def __init__(
    self,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    perspective_service: PerspectiveService,
    api_config_service: APIConfigService,
    suggestion_service: SuggestionService,
    generation_service: GenerationService,
    prompt_profile_service: PromptProfileService,
    typewriter_layout_service: TypewriterLayoutService,
  ) -> None:
    self._project_service = project_service
    self._chapter_service = chapter_service
    self._document_service = document_service
    self._perspective_service = perspective_service
    self._api_config_service = api_config_service
    self._suggestion_service = suggestion_service
    self._generation_service = generation_service
    self._prompt_profile_service = prompt_profile_service
    self._typewriter_layout_service = typewriter_layout_service

  async def get_workspace(
    self, project_id: str, chapter_id: str | None = None
  ) -> WorkspaceSnapshot:
    manifest = await self._project_service.get_manifest(project_id)
    sorted_chapters = sorted(manifest.chapters, key=lambda chapter: chapter.order)
    active_chapter_summary = (
      next((chapter for chapter in sorted_chapters if chapter.id == chapter_id), None)
      if chapter_id
      else sorted_chapters[0]
    )
    if active_chapter_summary is None:
      active_chapter_summary = sorted_chapters[0]
    active_chapter = await self._chapter_service.get_chapter(project_id, active_chapter_summary.id)
    perspectives = await self._perspective_service.list_perspectives(project_id)
    api_configs = await self._api_config_service.list_configs()
    generation_presets = await self._generation_service.list_presets(project_id)
    prompt_profiles = await self._prompt_profile_service.list_profiles(project_id)
    typewriter_layout_settings = await self._typewriter_layout_service.get_settings()
    chapter_tree = await self._chapter_service.list_chapter_tree(project_id)
    document_tree = await self._document_service.list_document_tree(project_id)

    return WorkspaceSnapshot(
      project=manifest,
      active_chapter=ActiveChapter(
        id=active_chapter.id,
        title=active_chapter.title,
        content=active_chapter.content,
        word_count=active_chapter.word_count,
        writing_synopsis=active_chapter.writing_synopsis,
        writing_synopsis_updated_at=active_chapter.writing_synopsis_updated_at,
        updated_at=active_chapter.updated_at,
      ),
      chapters=sorted_chapters,
      chapter_tree=chapter_tree,
      documents=manifest.documents,
      document_tree=document_tree,
      perspectives=perspectives,
      suggestions=[],
      api_configs=api_configs,
      generation_presets=generation_presets,
      prompt_profiles=prompt_profiles,
      typewriter_layout_settings=typewriter_layout_settings,
    )
