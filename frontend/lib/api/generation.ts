import { apiFetch } from "./client";
import type {
  GeneratedChapterBlueprint,
  GeneratedDraft,
  GenerateChapterBlueprintInput,
  GenerateDocumentContinuationInput,
  GenerateDraftInput,
  GenerateQuickDraftInput,
  GenerationPreset,
  GenerationPresetInput,
  GenerationPresetKind,
  GenerationPresetLibrary,
  GenerationPresetUpdate,
  PolishDocumentSelectionInput,
  PolishSelectionInput
} from "./types/index";

export async function getGenerationPresets(
  projectId: string,
): Promise<GenerationPresetLibrary> {
  return await apiFetch<GenerationPresetLibrary>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/presets`,
  );
}

export async function createGenerationPreset(
  projectId: string,
  input: GenerationPresetInput,
): Promise<GenerationPreset> {
  return await apiFetch<GenerationPreset>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/presets`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function updateGenerationPreset(
  projectId: string,
  kind: GenerationPresetKind,
  presetId: string,
  input: GenerationPresetUpdate,
): Promise<GenerationPreset> {
  return await apiFetch<GenerationPreset>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/presets/${encodeURIComponent(kind)}/${encodeURIComponent(presetId)}`,
    {
      method: "PUT",
      body: JSON.stringify(input),
    },
  );
}

export async function deleteGenerationPreset(
  projectId: string,
  kind: GenerationPresetKind,
  presetId: string,
): Promise<void> {
  await apiFetch<void>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/presets/${encodeURIComponent(kind)}/${encodeURIComponent(presetId)}`,
    {
      method: "DELETE",
    },
  );
}

export async function generateDraft(
  projectId: string,
  input: GenerateDraftInput,
): Promise<GeneratedDraft> {
  return await apiFetch<GeneratedDraft>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/draft`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function generateChapterBlueprint(
  projectId: string,
  input: GenerateChapterBlueprintInput,
): Promise<GeneratedChapterBlueprint> {
  return await apiFetch<GeneratedChapterBlueprint>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/chapter-blueprint`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function generateQuickDraft(
  projectId: string,
  input: GenerateQuickDraftInput,
): Promise<GeneratedDraft> {
  return await apiFetch<GeneratedDraft>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/quick-draft`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function polishSelection(
  projectId: string,
  input: PolishSelectionInput,
): Promise<GeneratedDraft> {
  return await apiFetch<GeneratedDraft>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/polish`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function polishDocumentSelection(
  projectId: string,
  input: PolishDocumentSelectionInput,
): Promise<GeneratedDraft> {
  return await apiFetch<GeneratedDraft>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/documents/polish`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function generateDocumentContinuation(
  projectId: string,
  input: GenerateDocumentContinuationInput,
): Promise<GeneratedDraft> {
  return await apiFetch<GeneratedDraft>(
    `/api/projects/${encodeURIComponent(projectId)}/generation/documents/continue`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}
