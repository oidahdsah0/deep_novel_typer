"use client";

import type { Dispatch, SetStateAction } from "react";
import type { DraftGenerationAction } from "@/lib/api/index";
import type {
  ChapterBlueprintDialogState,
  GenerationDialogState,
  PendingDraftGenerationState,
  PolishDialogState,
} from "../../types";
import type { DraftGenerationParams } from "./draftGenerationTypes";
import { useChapterBlueprintGeneration } from "./useChapterBlueprintGeneration";
import { usePendingDraft } from "./usePendingDraft";
import { usePolishGeneration } from "./usePolishGeneration";
import { useTextDraftGeneration } from "./useTextDraftGeneration";

export type DraftGenerationApi = {
  chapterBlueprintDialog: ChapterBlueprintDialogState;
  generationDialog: GenerationDialogState;
  handleAcceptChapterBlueprint: () => void;
  handleAcceptDraft: () => void;
  handleAcceptPolish: () => void;
  handleDiscardChapterBlueprint: () => void;
  handleDiscardDraft: () => void;
  handleDiscardPolish: () => void;
  handleGenerateChapterBlueprint: () => Promise<void>;
  handleGenerateDraft: () => Promise<void>;
  handleGeneratePolish: () => Promise<void>;
  handleGenerateQuickDraft: () => Promise<void>;
  handleOpenChapterBlueprintDialog: () => void;
  handleOpenGenerationDialog: (action: DraftGenerationAction) => void;
  handleOpenPolishDialog: () => void;
  isGeneratingChapterBlueprint: boolean;
  isGeneratingDraft: boolean;
  isPolishing: boolean;
  pendingDraftGeneration: PendingDraftGenerationState | null;
  polishDialog: PolishDialogState;
  setChapterBlueprintDialog: Dispatch<SetStateAction<ChapterBlueprintDialogState>>;
  setGenerationDialog: Dispatch<SetStateAction<GenerationDialogState>>;
  setPolishDialog: Dispatch<SetStateAction<PolishDialogState>>;
};

export function useDraftGeneration(params: DraftGenerationParams) {
  const {
    commitGeneratedContent,
    resource,
    setChapterSelection,
    setContent,
    setSelectionMenuPosition,
  } = params;

  const pendingDraftControls = usePendingDraft({
    commitGeneratedContent,
    resource,
    setChapterSelection,
    setContent,
    setSelectionMenuPosition,
  });
  const chapterBlueprint = useChapterBlueprintGeneration(params);
  const polish = usePolishGeneration(params);
  const textDraft = useTextDraftGeneration({
    chapterBlueprintDialog: chapterBlueprint.chapterBlueprintDialog,
    params,
    pendingDraftControls,
    polishDialog: polish.polishDialog,
  });

  function handleOpenChapterBlueprintDialog() {
    if (pendingDraftControls.pendingDraftGeneration) {
      return;
    }
    chapterBlueprint.handleOpenChapterBlueprintDialog();
  }

  return {
    chapterBlueprintDialog: chapterBlueprint.chapterBlueprintDialog,
    generationDialog: textDraft.generationDialog,
    handleAcceptChapterBlueprint: chapterBlueprint.handleAcceptChapterBlueprint,
    handleAcceptDraft: textDraft.handleAcceptDraft,
    handleAcceptPolish: polish.handleAcceptPolish,
    handleDiscardDraft: textDraft.handleDiscardDraft,
    handleDiscardChapterBlueprint: chapterBlueprint.handleDiscardChapterBlueprint,
    handleDiscardPolish: polish.handleDiscardPolish,
    handleGenerateChapterBlueprint: chapterBlueprint.handleGenerateChapterBlueprint,
    handleGenerateDraft: textDraft.handleGenerateDraft,
    handleGenerateQuickDraft: textDraft.handleGenerateQuickDraft,
    handleGeneratePolish: polish.handleGeneratePolish,
    handleOpenChapterBlueprintDialog,
    handleOpenGenerationDialog: textDraft.handleOpenGenerationDialog,
    handleOpenPolishDialog: polish.handleOpenPolishDialog,
    isGeneratingChapterBlueprint: chapterBlueprint.isGeneratingChapterBlueprint,
    isGeneratingDraft: textDraft.isGeneratingDraft,
    isPolishing: polish.isPolishing,
    pendingDraftGeneration: pendingDraftControls.pendingDraftGeneration,
    polishDialog: polish.polishDialog,
    setChapterBlueprintDialog: chapterBlueprint.setChapterBlueprintDialog,
    setGenerationDialog: textDraft.setGenerationDialog,
    setPolishDialog: polish.setPolishDialog,
  } satisfies DraftGenerationApi;
}
