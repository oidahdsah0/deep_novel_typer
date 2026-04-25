import type {
  DraftGenerationAction,
  GenerateChapterBlueprintInput,
  GenerateDraftInput,
  GenerateQuickDraftInput,
  GenerationPreset,
  GenerationPresetKind,
  GenerationPresetUpdate,
  PolishSelectionInput,
} from "@/lib/api/index";
import type { ChapterSelection, DraftInsertionContext } from "../../types";

type PresetSaveKey = (kind: GenerationPresetKind, presetId: string) => string;

function patchedPresetContent(
  patches: Record<string, GenerationPresetUpdate>,
  presetSaveKey: PresetSaveKey,
  kind: GenerationPresetKind,
  preset: GenerationPreset,
) {
  return patches[presetSaveKey(kind, preset.id)]?.content ?? preset.content;
}

type SharedPromptInput = {
  authorPreset: GenerationPreset;
  anchor: DraftInsertionContext;
  chapterId: string;
  patches: Record<string, GenerationPresetUpdate>;
  presetSaveKey: PresetSaveKey;
};

export function buildDraftInput({
  action,
  anchor,
  authorPreset,
  chapterId,
  patches,
  presetSaveKey,
  writingPreset,
}: SharedPromptInput & {
  action: DraftGenerationAction;
  writingPreset: GenerationPreset;
}): GenerateDraftInput {
  return {
    chapter_id: chapterId,
    action,
    cursor_index: anchor.cursorIndex,
    previous_paragraph: anchor.previousParagraph,
    next_paragraph: anchor.nextParagraph,
    writing_preset_id: writingPreset.id,
    writing_prompt: patchedPresetContent(patches, presetSaveKey, "writing_mode", writingPreset),
    author_preset_id: authorPreset.id,
    author_skill: patchedPresetContent(patches, presetSaveKey, "author_persona", authorPreset),
  };
}

export function buildQuickDraftInput({
  anchor,
  authorPreset,
  chapterId,
  patches,
  presetSaveKey,
  quickPreset,
}: SharedPromptInput & {
  quickPreset: GenerationPreset;
}): GenerateQuickDraftInput {
  return {
    chapter_id: chapterId,
    cursor_index: anchor.cursorIndex,
    previous_paragraph: anchor.previousParagraph,
    next_paragraph: anchor.nextParagraph,
    quick_preset_id: quickPreset.id,
    quick_prompt: "",
    author_preset_id: authorPreset.id,
    author_skill: patchedPresetContent(patches, presetSaveKey, "author_persona", authorPreset),
  };
}

export function buildChapterBlueprintInput({
  anchor,
  authorPreset,
  blueprintPreset,
  chapterId,
  patches,
  presetSaveKey,
}: SharedPromptInput & {
  blueprintPreset: GenerationPreset;
}): GenerateChapterBlueprintInput {
  return {
    chapter_id: chapterId,
    cursor_index: anchor.cursorIndex,
    previous_paragraph: anchor.previousParagraph,
    next_paragraph: anchor.nextParagraph,
    blueprint_preset_id: blueprintPreset.id,
    blueprint_prompt: patchedPresetContent(
      patches,
      presetSaveKey,
      "chapter_blueprint_mode",
      blueprintPreset,
    ),
    author_preset_id: authorPreset.id,
    author_skill: patchedPresetContent(patches, presetSaveKey, "author_persona", authorPreset),
  };
}

export function buildPolishInput({
  chapterId,
  patches,
  polishPreset,
  presetSaveKey,
  selection,
}: {
  chapterId: string;
  patches: Record<string, GenerationPresetUpdate>;
  polishPreset: GenerationPreset;
  presetSaveKey: PresetSaveKey;
  selection: ChapterSelection;
}): PolishSelectionInput {
  return {
    chapter_id: chapterId,
    selected_text: selection.text,
    polish_preset_id: polishPreset.id,
    polish_prompt: patchedPresetContent(patches, presetSaveKey, "polish_mode", polishPreset),
  };
}
