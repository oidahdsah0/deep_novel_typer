"use client";

import { useState } from "react";
import { polishSelection } from "@/lib/api/index";
import { useNotice } from "@/components/dialog";
import type { PolishDialogState } from "../../types";
import { generationErrorMessage } from "./draftGenerationErrors";
import type { DraftGenerationParams } from "./draftGenerationTypes";
import { buildPolishInput } from "./draftRequestBuilders";

export function usePolishGeneration({
  chapterSelection,
  commitGeneratedContent,
  content,
  flushPresetSave,
  flushChapterWritingSynopsis,
  onPolishAccepted,
  pendingPresetPatches,
  polishPresets,
  presetSaveKey,
  projectId,
  readChapterSelection,
  resource,
  saveActive,
  selectedPolishPreset,
  setChapterSelection,
  setSelectedPolishPresetId,
  setSelectionMenuPosition,
}: DraftGenerationParams) {
  const [polishDialog, setPolishDialog] = useState<PolishDialogState>(null);
  const [isPolishing, setIsPolishing] = useState(false);
  const notice = useNotice();

  function hideSelectionMenu() {
    setChapterSelection(null);
    setSelectionMenuPosition((current) =>
      current.visible ? { ...current, visible: false } : current,
    );
  }

  function handleOpenPolishDialog() {
    const selection = readChapterSelection() ?? chapterSelection;
    if (resource.type !== "chapter" || !selection) {
      return;
    }
    setChapterSelection(selection);
    setSelectedPolishPresetId(selectedPolishPreset?.id ?? polishPresets[0]?.id ?? "");
    setPolishDialog({ error: null, result: null });
  }

  async function handleGeneratePolish() {
    if (
      !polishDialog ||
      resource.type !== "chapter" ||
      !selectedPolishPreset ||
      !chapterSelection
    ) {
      return;
    }

    const input = buildPolishInput({
      chapterId: resource.id,
      patches: pendingPresetPatches.current,
      polishPreset: selectedPolishPreset,
      presetSaveKey,
      selection: chapterSelection,
    });

    setIsPolishing(true);
    setPolishDialog((current) => (current ? { ...current, error: null, result: null } : current));
    try {
      await Promise.all([
        flushPresetSave("polish_mode", selectedPolishPreset.id),
        flushChapterWritingSynopsis(),
        saveActive(content),
      ]);
      const result = await polishSelection(projectId, input);
      setPolishDialog((current) =>
        current ? { ...current, error: null, result } : current,
      );
    } catch (error) {
      setPolishDialog((current) =>
        current
          ? {
              ...current,
              error: generationErrorMessage(error),
              result: null,
            }
          : current,
      );
    } finally {
      setIsPolishing(false);
    }
  }

  function handleAcceptPolish() {
    if (!polishDialog?.result || !chapterSelection) {
      return;
    }
    const selection = chapterSelection;
    const resultText = polishDialog.result.text;
    const currentSelectionText = content.slice(selection.start, selection.end);
    if (currentSelectionText !== selection.text) {
      void notice("原选区内容已经变化，请重新选择文字后再润色。", {
        title: "选区已变化",
      });
      setPolishDialog(null);
      hideSelectionMenu();
      return;
    }
    const nextContent =
      content.slice(0, selection.start) + resultText + content.slice(selection.end);
    const nextSelectionEnd = selection.start + resultText.length;
    setPolishDialog(null);
    setChapterSelection(null);
    commitGeneratedContent(nextContent);
    onPolishAccepted(selection.start, nextSelectionEnd);
  }

  function handleDiscardPolish() {
    setPolishDialog(null);
    hideSelectionMenu();
  }

  return {
    handleAcceptPolish,
    handleDiscardPolish,
    handleGeneratePolish,
    handleOpenPolishDialog,
    isPolishing,
    polishDialog,
    setPolishDialog,
  };
}
