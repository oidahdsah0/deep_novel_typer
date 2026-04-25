from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.APIs.dependencies import get_generation_service
from app.Services.generation_service import GenerationService
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

router = APIRouter()


@router.get("/presets", response_model=GenerationPresetLibrary)
async def list_generation_presets(
  project_id: str,
  service: GenerationService = Depends(get_generation_service),
) -> GenerationPresetLibrary:
  return await service.list_presets(project_id)


@router.post(
  "/presets",
  response_model=GenerationPreset,
  status_code=status.HTTP_201_CREATED,
)
async def create_generation_preset(
  project_id: str,
  request: CreateGenerationPresetRequest,
  service: GenerationService = Depends(get_generation_service),
) -> GenerationPreset:
  return await service.create_preset(project_id, request)


@router.put("/presets/{kind}/{preset_id}", response_model=GenerationPreset)
async def update_generation_preset(
  project_id: str,
  kind: GenerationPresetKind,
  preset_id: str,
  request: UpdateGenerationPresetRequest,
  service: GenerationService = Depends(get_generation_service),
) -> GenerationPreset:
  return await service.update_preset(project_id, kind, preset_id, request)


@router.delete("/presets/{kind}/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generation_preset(
  project_id: str,
  kind: GenerationPresetKind,
  preset_id: str,
  service: GenerationService = Depends(get_generation_service),
) -> Response:
  await service.delete_preset(project_id, kind, preset_id)
  return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/draft", response_model=GeneratedDraft)
async def generate_draft(
  project_id: str,
  request: GenerateDraftRequest,
  service: GenerationService = Depends(get_generation_service),
) -> GeneratedDraft:
  return await service.generate_draft(project_id, request)


@router.post("/quick-draft", response_model=GeneratedDraft)
async def generate_quick_draft(
  project_id: str,
  request: GenerateQuickDraftRequest,
  service: GenerationService = Depends(get_generation_service),
) -> GeneratedDraft:
  return await service.generate_quick_draft(project_id, request)


@router.post("/chapter-blueprint", response_model=GeneratedChapterBlueprint)
async def generate_chapter_blueprint(
  project_id: str,
  request: GenerateChapterBlueprintRequest,
  service: GenerationService = Depends(get_generation_service),
) -> GeneratedChapterBlueprint:
  return await service.generate_chapter_blueprint(project_id, request)


@router.post("/polish", response_model=GeneratedDraft)
async def polish_selection(
  project_id: str,
  request: PolishSelectionRequest,
  service: GenerationService = Depends(get_generation_service),
) -> GeneratedDraft:
  return await service.polish_selection(project_id, request)


@router.post("/documents/polish", response_model=GeneratedDraft)
async def polish_document_selection(
  project_id: str,
  request: PolishDocumentSelectionRequest,
  service: GenerationService = Depends(get_generation_service),
) -> GeneratedDraft:
  return await service.polish_document_selection(project_id, request)


@router.post("/documents/continue", response_model=GeneratedDraft)
async def generate_document_continuation(
  project_id: str,
  request: GenerateDocumentContinuationRequest,
  service: GenerationService = Depends(get_generation_service),
) -> GeneratedDraft:
  return await service.generate_document_continuation(project_id, request)
