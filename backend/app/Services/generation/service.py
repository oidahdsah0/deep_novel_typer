from __future__ import annotations

from app.Schemas.common import GenerationPresetKind
from app.Schemas.generation import (
  CreateGenerationPresetRequest,
  GenerateChapterBlueprintRequest,
  GenerateDocumentContinuationRequest,
  GenerateDraftRequest,
  GenerateQuickDraftRequest,
  GeneratedChapterBlueprint,
  GeneratedDraft,
  GenerationPreset,
  GenerationPresetLibrary,
  PolishDocumentSelectionRequest,
  PolishSelectionRequest,
  UpdateGenerationPresetRequest,
)
from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.debug_log_service import DebugLogService
from app.Services.document_service import DocumentService
from app.Services.prompt_profiles import PromptProfileService
from app.Services.project_service import ProjectService
from app.Utils.config import GenerationPresetDefault
from app.Utils.db import AsyncDatabase
from app.Utils.llm import CompletionClient
from app.Utils.locks import AsyncLockRegistry

from .blueprint_actions import BlueprintGenerationActions
from .document_actions import DocumentGenerationActions
from .draft_actions import DraftGenerationActions
from .polish_actions import PolishGenerationActions
from .preset_resolution import GenerationPresetResolver
from .runtime import GenerationRuntime


class GenerationService:
  def __init__(
    self,
    db: AsyncDatabase,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    prompt_profile_service: PromptProfileService,
    api_config_service: APIConfigService,
    llm_client: CompletionClient,
    defaults: tuple[GenerationPresetDefault, ...],
    debug_log_service: DebugLogService | None = None,
  ) -> None:
    presets = GenerationPresetResolver(db, locks, project_service, defaults)
    runtime = GenerationRuntime(
      prompt_profile_service,
      api_config_service,
      llm_client,
      debug_log_service,
    )
    self._presets = presets
    self._draft_actions = DraftGenerationActions(
      project_service, chapter_service, presets, runtime
    )
    self._blueprint_actions = BlueprintGenerationActions(
      project_service, chapter_service, presets, runtime
    )
    self._polish_actions = PolishGenerationActions(
      project_service, chapter_service, presets, runtime
    )
    self._document_actions = DocumentGenerationActions(
      project_service, document_service, chapter_service, presets, runtime
    )

  async def list_presets(self, project_id: str) -> GenerationPresetLibrary:
    return await self._presets.list_presets(project_id)

  async def create_preset(
    self, project_id: str, request: CreateGenerationPresetRequest
  ) -> GenerationPreset:
    return await self._presets.create_preset(project_id, request)

  async def update_preset(
    self,
    project_id: str,
    kind: GenerationPresetKind,
    preset_id: str,
    request: UpdateGenerationPresetRequest,
  ) -> GenerationPreset:
    return await self._presets.update_preset(project_id, kind, preset_id, request)

  async def delete_preset(
    self, project_id: str, kind: GenerationPresetKind, preset_id: str
  ) -> None:
    await self._presets.delete_preset(project_id, kind, preset_id)

  async def generate_draft(
    self, project_id: str, request: GenerateDraftRequest
  ) -> GeneratedDraft:
    return await self._draft_actions.generate_draft(project_id, request)

  async def generate_quick_draft(
    self, project_id: str, request: GenerateQuickDraftRequest
  ) -> GeneratedDraft:
    return await self._draft_actions.generate_quick_draft(project_id, request)

  async def generate_chapter_blueprint(
    self, project_id: str, request: GenerateChapterBlueprintRequest
  ) -> GeneratedChapterBlueprint:
    return await self._blueprint_actions.generate_chapter_blueprint(project_id, request)

  async def polish_selection(
    self, project_id: str, request: PolishSelectionRequest
  ) -> GeneratedDraft:
    return await self._polish_actions.polish_selection(project_id, request)

  async def polish_document_selection(
    self, project_id: str, request: PolishDocumentSelectionRequest
  ) -> GeneratedDraft:
    return await self._document_actions.polish_document_selection(project_id, request)

  async def generate_document_continuation(
    self, project_id: str, request: GenerateDocumentContinuationRequest
  ) -> GeneratedDraft:
    return await self._document_actions.generate_document_continuation(
      project_id, request
    )
