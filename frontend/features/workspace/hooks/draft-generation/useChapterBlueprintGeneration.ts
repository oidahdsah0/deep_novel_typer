"use client";

import { useState } from "react";
import { generateChapterBlueprint } from "@/lib/api/index";
import {
  insertGeneratedTextWithRange,
  renderChapterBlueprintPoints,
} from "../../utils";
import type { ChapterBlueprintDialogState } from "../../types";
import { generationErrorMessage } from "./draftGenerationErrors";
import type { DraftGenerationParams } from "./draftGenerationTypes";
import { buildChapterBlueprintInput } from "./draftRequestBuilders";

export function useChapterBlueprintGeneration({
  authorPresets,
  chapterBlueprintPresets,
  commitGeneratedContent,
  content,
  flushPresetSave,
  flushChapterWritingSynopsis,
  pendingPresetPatches,
  presetSaveKey,
  projectId,
  readDraftInsertionContext,
  resource,
  saveActive,
  selectedAuthorPreset,
  selectedChapterBlueprintPreset,
  setSelectedAuthorPresetId,
  setSelectedChapterBlueprintPresetId,
}: DraftGenerationParams) {
  const [chapterBlueprintDialog, setChapterBlueprintDialog] =
    useState<ChapterBlueprintDialogState>(null);
  const [isGeneratingChapterBlueprint, setIsGeneratingChapterBlueprint] = useState(false);

  function handleOpenChapterBlueprintDialog() {
    if (resource.type !== "chapter") {
      return;
    }
    setSelectedChapterBlueprintPresetId(
      selectedChapterBlueprintPreset?.id ?? chapterBlueprintPresets[0]?.id ?? "",
    );
    setSelectedAuthorPresetId(selectedAuthorPreset?.id ?? authorPresets[0]?.id ?? "");
    setChapterBlueprintDialog({
      anchor: readDraftInsertionContext(),
      error: null,
      result: null,
    });
  }

  async function handleGenerateChapterBlueprint() {
    if (
      !chapterBlueprintDialog ||
      resource.type !== "chapter" ||
      !selectedChapterBlueprintPreset ||
      !selectedAuthorPreset
    ) {
      return;
    }

    const input = buildChapterBlueprintInput({
      anchor: chapterBlueprintDialog.anchor,
      authorPreset: selectedAuthorPreset,
      blueprintPreset: selectedChapterBlueprintPreset,
      chapterId: resource.id,
      patches: pendingPresetPatches.current,
      presetSaveKey,
    });

    setIsGeneratingChapterBlueprint(true);
    setChapterBlueprintDialog((current) =>
      current ? { ...current, error: null, result: null } : current,
    );
    try {
      await Promise.all([
        flushPresetSave("chapter_blueprint_mode", selectedChapterBlueprintPreset.id),
        flushPresetSave("author_persona", selectedAuthorPreset.id),
        flushChapterWritingSynopsis(),
        saveActive(content),
      ]);
      const result = await generateChapterBlueprint(projectId, input);
      setChapterBlueprintDialog((current) =>
        current ? { ...current, error: null, result } : current,
      );
    } catch (error) {
      setChapterBlueprintDialog((current) =>
        current
          ? {
              ...current,
              error: generationErrorMessage(error),
              result: null,
            }
          : current,
      );
    } finally {
      setIsGeneratingChapterBlueprint(false);
    }
  }

  function handleAcceptChapterBlueprint() {
    if (!chapterBlueprintDialog?.result) {
      return;
    }
    const rendered = renderChapterBlueprintPoints(chapterBlueprintDialog.result.points);
    const inserted = insertGeneratedTextWithRange(
      content,
      rendered,
      chapterBlueprintDialog.anchor.cursorIndex,
    );
    if (!inserted) {
      setChapterBlueprintDialog((current) =>
        current
          ? { ...current, error: "模型没有返回可插入的基础铺设要点。", result: null }
          : current,
      );
      return;
    }
    const nextContent = inserted.nextContent;
    setChapterBlueprintDialog(null);
    commitGeneratedContent(nextContent);
  }

  function handleDiscardChapterBlueprint() {
    setChapterBlueprintDialog(null);
  }

  return {
    chapterBlueprintDialog,
    handleAcceptChapterBlueprint,
    handleDiscardChapterBlueprint,
    handleGenerateChapterBlueprint,
    handleOpenChapterBlueprintDialog,
    isGeneratingChapterBlueprint,
    setChapterBlueprintDialog,
  };
}
