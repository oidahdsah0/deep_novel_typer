"use client";

import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import { useState } from "react";
import {
  generateDocumentContinuation,
  polishDocumentSelection,
  type GenerationPreset,
  type GenerationPresetKind,
  type GenerationPresetUpdate,
} from "@/lib/api/index";
import { useNotice } from "@/components/dialog";
import { generationErrorMessage } from "../generationErrors";
import { appendGeneratedText } from "../utils";
import type {
  ActiveResource,
  ChapterSelection,
  DocumentGenerationDialogState,
} from "../types";

export type DocumentGenerationApi = {
  documentGenerationDialog: DocumentGenerationDialogState;
  handleAcceptDocumentGeneration: () => void;
  handleDiscardDocumentGeneration: () => void;
  handleGenerateDocument: () => Promise<void>;
  handleOpenDocumentContinuationDialog: () => void;
  handleOpenDocumentPolishDialog: () => void;
  isGeneratingDocument: boolean;
  setDocumentGenerationDialog: Dispatch<SetStateAction<DocumentGenerationDialogState>>;
};

export function useDocumentGeneration({
  activeChapterId,
  commitGeneratedContent,
  content,
  documentGenerationPresets,
  documentPolishPresets,
  documentSelection,
  editorPresets,
  flushPresetSave,
  flushChapterWritingSynopsis,
  pendingPresetPatches,
  presetSaveKey,
  projectId,
  resource,
  saveActive,
  selectedDocumentGenerationPreset,
  selectedDocumentPolishPreset,
  selectedEditorPreset,
  setDocumentSelection,
  setSelectedDocumentGenerationPresetId,
  setSelectedDocumentPolishPresetId,
  setSelectedEditorPresetId,
}: {
  activeChapterId: string;
  commitGeneratedContent: (nextContent: string) => void;
  content: string;
  documentGenerationPresets: GenerationPreset[];
  documentPolishPresets: GenerationPreset[];
  documentSelection: ChapterSelection | null;
  editorPresets: GenerationPreset[];
  flushPresetSave: (kind: GenerationPresetKind, presetId: string) => Promise<void>;
  flushChapterWritingSynopsis: () => Promise<void>;
  pendingPresetPatches: MutableRefObject<Record<string, GenerationPresetUpdate>>;
  presetSaveKey: (kind: GenerationPresetKind, presetId: string) => string;
  projectId: string;
  resource: ActiveResource;
  saveActive: (nextContent?: string) => Promise<void>;
  selectedDocumentGenerationPreset: GenerationPreset | undefined;
  selectedDocumentPolishPreset: GenerationPreset | undefined;
  selectedEditorPreset: GenerationPreset | undefined;
  setDocumentSelection: Dispatch<SetStateAction<ChapterSelection | null>>;
  setSelectedDocumentGenerationPresetId: Dispatch<SetStateAction<string>>;
  setSelectedDocumentPolishPresetId: Dispatch<SetStateAction<string>>;
  setSelectedEditorPresetId: Dispatch<SetStateAction<string>>;
}) {
  const [documentGenerationDialog, setDocumentGenerationDialog] =
    useState<DocumentGenerationDialogState>(null);
  const [isGeneratingDocument, setIsGeneratingDocument] = useState(false);
  const notice = useNotice();

  function handleOpenDocumentPolishDialog() {
    if (resource.type !== "document" || !documentSelection) {
      return;
    }
    setSelectedDocumentPolishPresetId(
      selectedDocumentPolishPreset?.id ?? documentPolishPresets[0]?.id ?? "",
    );
    setSelectedEditorPresetId(selectedEditorPreset?.id ?? editorPresets[0]?.id ?? "");
    setDocumentGenerationDialog({ action: "polish_selection", error: null, result: null });
  }

  function handleOpenDocumentContinuationDialog() {
    if (resource.type !== "document") {
      return;
    }
    setSelectedDocumentGenerationPresetId(
      selectedDocumentGenerationPreset?.id ?? documentGenerationPresets[0]?.id ?? "",
    );
    setSelectedEditorPresetId(selectedEditorPreset?.id ?? editorPresets[0]?.id ?? "");
    setDocumentGenerationDialog({ action: "continue_document", error: null, result: null });
  }

  async function handleGenerateDocument() {
    if (!documentGenerationDialog || resource.type !== "document" || !selectedEditorPreset) {
      return;
    }

    const editorSaveKey = presetSaveKey("editor_persona", selectedEditorPreset.id);
    const editorSkill =
      pendingPresetPatches.current[editorSaveKey]?.content ?? selectedEditorPreset.content;

    setIsGeneratingDocument(true);
    setDocumentGenerationDialog((current) =>
      current ? { ...current, error: null, result: null } : current,
    );
    try {
      if (documentGenerationDialog.action === "polish_selection") {
        if (!selectedDocumentPolishPreset || !documentSelection) {
          return;
        }
        const polishSaveKey = presetSaveKey(
          "document_polish_mode",
          selectedDocumentPolishPreset.id,
        );
        const polishPrompt =
          pendingPresetPatches.current[polishSaveKey]?.content ??
          selectedDocumentPolishPreset.content;
        await Promise.all([
          flushPresetSave("document_polish_mode", selectedDocumentPolishPreset.id),
          flushPresetSave("editor_persona", selectedEditorPreset.id),
          flushChapterWritingSynopsis(),
          saveActive(content),
        ]);
        const result = await polishDocumentSelection(projectId, {
          document_id: resource.id,
          chapter_id: activeChapterId,
          selected_text: documentSelection.text,
          polish_preset_id: selectedDocumentPolishPreset.id,
          polish_prompt: polishPrompt,
          editor_preset_id: selectedEditorPreset.id,
          editor_skill: editorSkill,
        });
        setDocumentGenerationDialog((current) =>
          current ? { ...current, error: null, result } : current,
        );
        return;
      }

      if (!selectedDocumentGenerationPreset) {
        return;
      }
      const generationSaveKey = presetSaveKey(
        "document_generation_mode",
        selectedDocumentGenerationPreset.id,
      );
      const generationPrompt =
        pendingPresetPatches.current[generationSaveKey]?.content ??
        selectedDocumentGenerationPreset.content;
      await Promise.all([
        flushPresetSave("document_generation_mode", selectedDocumentGenerationPreset.id),
        flushPresetSave("editor_persona", selectedEditorPreset.id),
        flushChapterWritingSynopsis(),
        saveActive(content),
      ]);
      const result = await generateDocumentContinuation(projectId, {
        document_id: resource.id,
        chapter_id: activeChapterId,
        generation_preset_id: selectedDocumentGenerationPreset.id,
        generation_prompt: generationPrompt,
        editor_preset_id: selectedEditorPreset.id,
        editor_skill: editorSkill,
      });
      setDocumentGenerationDialog((current) =>
        current ? { ...current, error: null, result } : current,
      );
    } catch (error) {
      setDocumentGenerationDialog((current) =>
        current
          ? {
              ...current,
              error: generationErrorMessage(error),
              result: null,
            }
          : current,
      );
    } finally {
      setIsGeneratingDocument(false);
    }
  }

  function handleAcceptDocumentGeneration() {
    if (!documentGenerationDialog?.result || resource.type !== "document") {
      return;
    }
    const resultText = documentGenerationDialog.result.text;
    let nextContent = content;
    if (documentGenerationDialog.action === "polish_selection") {
      const selection = documentSelection;
      if (!selection) {
        return;
      }
      const currentSelectionText = content.slice(selection.start, selection.end);
      if (currentSelectionText !== selection.text) {
        void notice("原选区内容已经变化，请重新选择资料文字后再润色。", {
          title: "选区已变化",
        });
        setDocumentGenerationDialog(null);
        setDocumentSelection(null);
        return;
      }
      nextContent =
        content.slice(0, selection.start) + resultText + content.slice(selection.end);
    } else {
      nextContent = appendGeneratedText(content, resultText);
    }

    setDocumentGenerationDialog(null);
    setDocumentSelection(null);
    commitGeneratedContent(nextContent);
  }

  function handleDiscardDocumentGeneration() {
    if (documentGenerationDialog?.action === "continue_document") {
      setDocumentGenerationDialog((current) => (current ? { ...current, result: null } : current));
      return;
    }
    setDocumentGenerationDialog(null);
    setDocumentSelection(null);
  }

  return {
    documentGenerationDialog,
    handleAcceptDocumentGeneration,
    handleDiscardDocumentGeneration,
    handleGenerateDocument,
    handleOpenDocumentContinuationDialog,
    handleOpenDocumentPolishDialog,
    isGeneratingDocument,
    setDocumentGenerationDialog,
  } satisfies DocumentGenerationApi;
}
