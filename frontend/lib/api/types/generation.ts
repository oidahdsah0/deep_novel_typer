import type { DraftGenerationAction, GenerationPresetKind } from "./common";

export type GenerationPreset = {
  id: string;
  kind: GenerationPresetKind;
  name: string;
  content: string;
  is_system: boolean;
  is_hidden: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type GenerationPresetLibrary = {
  writing_modes: GenerationPreset[];
  quick_generation_modes: GenerationPreset[];
  chapter_blueprint_modes: GenerationPreset[];
  author_personas: GenerationPreset[];
  polish_modes: GenerationPreset[];
  document_polish_modes: GenerationPreset[];
  document_generation_modes: GenerationPreset[];
  editor_personas: GenerationPreset[];
};

export type GenerationPresetInput = {
  kind: GenerationPresetKind;
  name: string;
  content?: string;
};

export type GenerationPresetUpdate = {
  name?: string;
  content?: string;
};

export type GenerateDraftInput = {
  chapter_id: string;
  action: DraftGenerationAction;
  cursor_index?: number;
  previous_paragraph?: string;
  next_paragraph?: string;
  writing_preset_id: string;
  writing_prompt: string;
  author_preset_id: string;
  author_skill: string;
};

export type GenerateChapterBlueprintInput = {
  chapter_id: string;
  cursor_index?: number;
  previous_paragraph?: string;
  next_paragraph?: string;
  blueprint_preset_id: string;
  blueprint_prompt: string;
  author_preset_id: string;
  author_skill: string;
};

export type GenerateQuickDraftInput = {
  chapter_id: string;
  cursor_index?: number;
  previous_paragraph?: string;
  next_paragraph?: string;
  quick_preset_id: string;
  quick_prompt: string;
  author_preset_id: string;
  author_skill: string;
};

export type PolishSelectionInput = {
  chapter_id: string;
  selected_text: string;
  polish_preset_id: string;
  polish_prompt: string;
};

export type PolishDocumentSelectionInput = {
  document_id: string;
  chapter_id?: string | null;
  selected_text: string;
  polish_preset_id: string;
  polish_prompt: string;
  editor_preset_id: string;
  editor_skill: string;
};

export type GenerateDocumentContinuationInput = {
  document_id: string;
  chapter_id?: string | null;
  generation_preset_id: string;
  generation_prompt: string;
  editor_preset_id: string;
  editor_skill: string;
};

export type GeneratedDraft = {
  text: string;
  source: "llm" | "local";
  model: string | null;
};

export type GeneratedChapterBlueprint = {
  points: string[];
  source: "llm" | "local";
  model: string | null;
};
