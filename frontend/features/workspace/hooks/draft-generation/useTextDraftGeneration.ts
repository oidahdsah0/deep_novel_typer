"use client";

import type { Dispatch, SetStateAction } from "react";
import { useState } from "react";
import {
  generateDraft,
  generateQuickDraft,
  type DraftGenerationAction,
} from "@/lib/api/index";
import { insertGeneratedTextWithRange } from "../../utils";
import type {
  ChapterBlueprintDialogState,
  GenerationDialogState,
  PendingDraftGenerationState,
  PolishDialogState,
} from "../../types";
import type { DraftGenerationParams } from "./draftGenerationTypes";
import { buildDraftInput, buildQuickDraftInput } from "./draftRequestBuilders";
import { useGeneratedDraftCommitter } from "./useGeneratedDraftCommitter";

type PendingDraftControls = {
  acceptPendingDraft: () => boolean;
  discardPendingDraft: () => boolean;
  pendingDraftGeneration: PendingDraftGenerationState | null;
  setPendingDraftGeneration: Dispatch<SetStateAction<PendingDraftGenerationState | null>>;
};

export function useTextDraftGeneration({
  chapterBlueprintDialog,
  params,
  pendingDraftControls,
  polishDialog,
}: {
  chapterBlueprintDialog: ChapterBlueprintDialogState;
  params: DraftGenerationParams;
  pendingDraftControls: PendingDraftControls;
  polishDialog: PolishDialogState;
}) {
  const {
    authorPresets,
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
    selectedQuickGenerationPreset,
    selectedWritingPreset,
    setContent,
    setSelectedAuthorPresetId,
    setSelectedWritingPresetId,
    writingPresets,
  } = params;
  const [generationDialog, setGenerationDialog] = useState<GenerationDialogState>(null);
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const { acceptPendingDraft, discardPendingDraft, pendingDraftGeneration, setPendingDraftGeneration } = pendingDraftControls;
  const { commitGeneratedDraft, setDraftError } = useGeneratedDraftCommitter({
    commitGeneratedContent,
    resource,
    setContent,
    setPendingDraftGeneration,
  });

  function handleOpenGenerationDialog(action: DraftGenerationAction) {
    if (resource.type !== "chapter" || pendingDraftGeneration) {
      return;
    }
    setSelectedWritingPresetId(selectedWritingPreset?.id ?? writingPresets[0]?.id ?? "");
    setSelectedAuthorPresetId(selectedAuthorPreset?.id ?? authorPresets[0]?.id ?? "");
    setGenerationDialog({
      action,
      anchor: readDraftInsertionContext(),
      error: null,
      result: null,
    });
  }

  async function handleGenerateDraft() {
    if (
      !generationDialog ||
      resource.type !== "chapter" ||
      !selectedWritingPreset ||
      !selectedAuthorPreset
    ) {
      return;
    }

    const action = generationDialog.action;
    const anchor = generationDialog.anchor;
    const chapterId = resource.id;
    const baseContent = content;
    const input = buildDraftInput({
      action,
      anchor,
      authorPreset: selectedAuthorPreset,
      chapterId,
      patches: pendingPresetPatches.current,
      presetSaveKey,
      writingPreset: selectedWritingPreset,
    });

    setIsGeneratingDraft(true);
    setGenerationDialog(null);
    setPendingDraftGeneration({
      action,
      chapterId,
      cursorIndex: anchor.cursorIndex,
      status: "generating",
    });
    try {
      await Promise.all([
        flushPresetSave("writing_mode", selectedWritingPreset.id),
        flushPresetSave("author_persona", selectedAuthorPreset.id),
        flushChapterWritingSynopsis(),
        saveActive(baseContent),
      ]);
      const result = await generateDraft(projectId, input);
      commitGeneratedDraft({
        action,
        baseContent,
        chapterId,
        cursorIndex: anchor.cursorIndex,
        result,
      });
    } catch (error) {
      setDraftError({ action, chapterId, error });
    } finally {
      setIsGeneratingDraft(false);
    }
  }

  async function handleGenerateQuickDraft() {
    if (
      resource.type !== "chapter" ||
      pendingDraftGeneration ||
      generationDialog ||
      chapterBlueprintDialog ||
      polishDialog ||
      !selectedQuickGenerationPreset ||
      !selectedAuthorPreset
    ) {
      return;
    }

    const anchor = readDraftInsertionContext();
    const chapterId = resource.id;
    const baseContent = content;
    const input = buildQuickDraftInput({
      anchor,
      authorPreset: selectedAuthorPreset,
      chapterId,
      patches: pendingPresetPatches.current,
      presetSaveKey,
      quickPreset: selectedQuickGenerationPreset,
    });

    setIsGeneratingDraft(true);
    setPendingDraftGeneration({
      action: "quick_next_paragraph",
      chapterId,
      cursorIndex: anchor.cursorIndex,
      status: "generating",
    });
    try {
      await Promise.all([
        flushPresetSave("author_persona", selectedAuthorPreset.id),
        flushChapterWritingSynopsis(),
        saveActive(baseContent),
      ]);
      const result = await generateQuickDraft(projectId, input);
      commitGeneratedDraft({
        action: "quick_next_paragraph",
        baseContent,
        chapterId,
        cursorIndex: anchor.cursorIndex,
        result,
      });
    } catch (error) {
      setDraftError({ action: "quick_next_paragraph", chapterId, error });
    } finally {
      setIsGeneratingDraft(false);
    }
  }

  function handleAcceptDraft() {
    if (acceptPendingDraft()) {
      return;
    }
    if (!generationDialog?.result) {
      return;
    }
    const inserted = insertGeneratedTextWithRange(
      content,
      generationDialog.result.text,
      generationDialog.anchor.cursorIndex,
    );
    if (!inserted) {
      setGenerationDialog((current) =>
        current ? { ...current, error: "模型没有返回可插入的正文。", result: null } : current,
      );
      return;
    }
    const nextContent = inserted.nextContent;
    setGenerationDialog(null);
    commitGeneratedContent(nextContent);
  }

  function handleDiscardDraft() {
    if (discardPendingDraft()) {
      return;
    }
    setGenerationDialog((current) => (current ? { ...current, result: null } : current));
  }

  return {
    generationDialog,
    handleAcceptDraft,
    handleDiscardDraft,
    handleGenerateDraft,
    handleGenerateQuickDraft,
    handleOpenGenerationDialog,
    isGeneratingDraft,
    setGenerationDialog,
  };
}
