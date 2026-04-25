"use client";

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useState } from "react";
import type { WorkspaceSnapshot } from "@/lib/api/index";
import { readTabQuickGenerationEnabled } from "../shortcutSettings";
import type {
  ActiveResource,
  PendingDraftGenerationState,
  WritingEditorKeyEvent,
} from "../types";
import {
  isDraftConfirmationActive,
  pendingDraftForResource,
} from "../workspaceGenerationControllerState";
import type { PromptProfilesApi, WorkspaceEditorApi } from "./workspaceInteractionApiTypes";
import { useDocumentGeneration, type DocumentGenerationApi } from "./useDocumentGeneration";
import { useDraftGeneration, type DraftGenerationApi } from "./useDraftGeneration";
import { useGenerationPresets, type GenerationPresetsApi } from "./useGenerationPresets";
import { usePromptPreview, type PromptPreviewApi } from "./usePromptPreview";
import type { WorkspaceResourceControllerApi } from "./useWorkspaceResourceController";

type UseWorkspaceGenerationControllerOptions = {
  content: string;
  editor: WorkspaceEditorApi;
  flushChapterWritingSynopsis: () => Promise<void>;
  projectId: string;
  promptProfiles: PromptProfilesApi;
  resource: ActiveResource;
  resourceController: WorkspaceResourceControllerApi;
  saveActive: (nextContent?: string) => Promise<void>;
  setContent: Dispatch<SetStateAction<string>>;
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
  workspace: WorkspaceSnapshot;
};

export type WorkspaceGenerationControllerApi = {
  documentGeneration: DocumentGenerationApi;
  draftGeneration: DraftGenerationApi;
  generationPresets: GenerationPresetsApi;
  handleChapterKeyDown: (event: WritingEditorKeyEvent) => void;
  isDraftConfirmationActive: boolean;
  pendingDraft: PendingDraftGenerationState | null;
  promptPreview: PromptPreviewApi;
};

export function useWorkspaceGenerationController({
  content,
  editor,
  flushChapterWritingSynopsis,
  projectId,
  promptProfiles,
  resource,
  resourceController,
  saveActive,
  setContent,
  setWorkspace,
  workspace,
}: UseWorkspaceGenerationControllerOptions) {
  const [isTabQuickGenerationEnabled, setIsTabQuickGenerationEnabled] = useState(false);
  const generationPresets = useGenerationPresets({
    generationPresets: workspace.generation_presets,
    projectId,
    setWorkspace,
  });
  const draftGeneration = useDraftGeneration({
    authorPresets: generationPresets.authorPresets,
    chapterBlueprintPresets: generationPresets.chapterBlueprintPresets,
    chapterSelection: editor.chapterSelection,
    content,
    commitGeneratedContent: resourceController.commitGeneratedContent,
    flushPresetSave: generationPresets.flushPresetSave,
    flushChapterWritingSynopsis,
    pendingPresetPatches: generationPresets.pendingPresetPatches,
    polishPresets: generationPresets.polishPresets,
    onPolishAccepted: editor.handlePolishAcceptedSelection,
    presetSaveKey: generationPresets.presetSaveKey,
    projectId,
    quickGenerationPresets: generationPresets.quickGenerationPresets,
    readDraftInsertionContext: editor.readDraftInsertionContext,
    readChapterSelection: editor.readChapterSelection,
    resource,
    saveActive,
    selectedAuthorPreset: generationPresets.selectedAuthorPreset,
    selectedChapterBlueprintPreset: generationPresets.selectedChapterBlueprintPreset,
    selectedPolishPreset: generationPresets.selectedPolishPreset,
    selectedQuickGenerationPreset: generationPresets.selectedQuickGenerationPreset,
    selectedWritingPreset: generationPresets.selectedWritingPreset,
    setChapterSelection: editor.setChapterSelection,
    setContent,
    setSelectedAuthorPresetId: generationPresets.setSelectedAuthorPresetId,
    setSelectedChapterBlueprintPresetId: generationPresets.setSelectedChapterBlueprintPresetId,
    setSelectedPolishPresetId: generationPresets.setSelectedPolishPresetId,
    setSelectedQuickGenerationPresetId: generationPresets.setSelectedQuickGenerationPresetId,
    setSelectedWritingPresetId: generationPresets.setSelectedWritingPresetId,
    setSelectionMenuPosition: editor.setSelectionMenuPosition,
    writingPresets: generationPresets.writingPresets,
  });
  const documentGeneration = useDocumentGeneration({
    commitGeneratedContent: resourceController.commitGeneratedContent,
    content,
    documentGenerationPresets: generationPresets.documentGenerationPresets,
    documentPolishPresets: generationPresets.documentPolishPresets,
    documentSelection: editor.documentSelection,
    editorPresets: generationPresets.editorPresets,
    activeChapterId: workspace.active_chapter.id,
    flushPresetSave: generationPresets.flushPresetSave,
    flushChapterWritingSynopsis,
    pendingPresetPatches: generationPresets.pendingPresetPatches,
    presetSaveKey: generationPresets.presetSaveKey,
    projectId,
    resource,
    saveActive,
    selectedDocumentGenerationPreset: generationPresets.selectedDocumentGenerationPreset,
    selectedDocumentPolishPreset: generationPresets.selectedDocumentPolishPreset,
    selectedEditorPreset: generationPresets.selectedEditorPreset,
    setDocumentSelection: editor.setDocumentSelection,
    setSelectedDocumentGenerationPresetId: generationPresets.setSelectedDocumentGenerationPresetId,
    setSelectedDocumentPolishPresetId: generationPresets.setSelectedDocumentPolishPresetId,
    setSelectedEditorPresetId: generationPresets.setSelectedEditorPresetId,
  });
  const promptPreview = usePromptPreview({
    buildPromptProfileOverride: promptProfiles.buildPromptProfileOverride,
    chapterSelection: editor.chapterSelection,
    content,
    documentSelection: editor.documentSelection,
    pendingPresetPatches: generationPresets.pendingPresetPatches,
    presetSaveKey: generationPresets.presetSaveKey,
    projectId,
    promptDraft: promptProfiles.promptDraft,
    readDraftInsertionContext: editor.readDraftInsertionContext,
    resource,
    saveActive,
    flushChapterWritingSynopsis,
    selectedAuthorPreset: generationPresets.selectedAuthorPreset,
    selectedChapterBlueprintPreset: generationPresets.selectedChapterBlueprintPreset,
    selectedDocumentGenerationPreset: generationPresets.selectedDocumentGenerationPreset,
    selectedDocumentPolishPreset: generationPresets.selectedDocumentPolishPreset,
    selectedEditorPreset: generationPresets.selectedEditorPreset,
    selectedPolishPreset: generationPresets.selectedPolishPreset,
    selectedWritingPreset: generationPresets.selectedWritingPreset,
    setPromptSaveState: promptProfiles.setPromptSaveState,
    workspace,
  });
  const pendingDraft = pendingDraftForResource(
    resource,
    draftGeneration.pendingDraftGeneration,
  );
  const isDraftConfirmationActiveValue = isDraftConfirmationActive(pendingDraft);
  const { setChapterBlueprintDialog, setPolishDialog } = draftGeneration;
  const { setDocumentGenerationDialog } = documentGeneration;

  useEffect(() => setIsTabQuickGenerationEnabled(readTabQuickGenerationEnabled()), []);

  useEffect(() => {
    setChapterBlueprintDialog(null);
    setPolishDialog(null);
    setDocumentGenerationDialog(null);
  }, [
    resource.id,
    resource.type,
    setChapterBlueprintDialog,
    setDocumentGenerationDialog,
    setPolishDialog,
  ]);

  function handleChapterKeyDown(event: WritingEditorKeyEvent) {
    if (
      event.key !== "Tab" ||
      event.shiftKey ||
      event.altKey ||
      event.ctrlKey ||
      event.metaKey ||
      event.nativeEvent.isComposing ||
      !isTabQuickGenerationEnabled ||
      isDraftConfirmationActiveValue ||
      draftGeneration.generationDialog ||
      draftGeneration.chapterBlueprintDialog ||
      draftGeneration.polishDialog
    ) {
      return;
    }
    event.preventDefault();
    void draftGeneration.handleGenerateQuickDraft();
  }

  return {
    documentGeneration,
    draftGeneration,
    generationPresets,
    handleChapterKeyDown,
    isDraftConfirmationActive: isDraftConfirmationActiveValue,
    pendingDraft,
    promptPreview,
  } satisfies WorkspaceGenerationControllerApi;
}
