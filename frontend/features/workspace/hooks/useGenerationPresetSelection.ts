"use client";

import { useEffect, useState } from "react";
import type { GenerationPreset, GenerationPresetKind } from "@/lib/api/index";

export function useGenerationPresetSelection({
  authorPresets,
  chapterBlueprintPresets,
  documentGenerationPresets,
  documentPolishPresets,
  editorPresets,
  polishPresets,
  quickGenerationPresets,
  writingPresets,
}: {
  authorPresets: GenerationPreset[];
  chapterBlueprintPresets: GenerationPreset[];
  documentGenerationPresets: GenerationPreset[];
  documentPolishPresets: GenerationPreset[];
  editorPresets: GenerationPreset[];
  polishPresets: GenerationPreset[];
  quickGenerationPresets: GenerationPreset[];
  writingPresets: GenerationPreset[];
}) {
  const [selectedWritingPresetId, setSelectedWritingPresetId] = useState(
    writingPresets[0]?.id ?? "",
  );
  const [selectedQuickGenerationPresetId, setSelectedQuickGenerationPresetId] = useState(
    quickGenerationPresets[0]?.id ?? "",
  );
  const [selectedAuthorPresetId, setSelectedAuthorPresetId] = useState(
    authorPresets[0]?.id ?? "",
  );
  const [selectedChapterBlueprintPresetId, setSelectedChapterBlueprintPresetId] = useState(
    chapterBlueprintPresets[0]?.id ?? "",
  );
  const [selectedPolishPresetId, setSelectedPolishPresetId] = useState(
    polishPresets[0]?.id ?? "",
  );
  const [selectedDocumentPolishPresetId, setSelectedDocumentPolishPresetId] = useState(
    documentPolishPresets[0]?.id ?? "",
  );
  const [selectedDocumentGenerationPresetId, setSelectedDocumentGenerationPresetId] =
    useState(documentGenerationPresets[0]?.id ?? "");
  const [selectedEditorPresetId, setSelectedEditorPresetId] = useState(
    editorPresets[0]?.id ?? "",
  );

  const selectedWritingPreset =
    writingPresets.find((preset) => preset.id === selectedWritingPresetId) ??
    writingPresets[0];
  const selectedQuickGenerationPreset =
    quickGenerationPresets.find((preset) => preset.id === selectedQuickGenerationPresetId) ??
    quickGenerationPresets[0];
  const selectedAuthorPreset =
    authorPresets.find((preset) => preset.id === selectedAuthorPresetId) ??
    authorPresets[0];
  const selectedChapterBlueprintPreset =
    chapterBlueprintPresets.find((preset) => preset.id === selectedChapterBlueprintPresetId) ??
    chapterBlueprintPresets[0];
  const selectedPolishPreset =
    polishPresets.find((preset) => preset.id === selectedPolishPresetId) ??
    polishPresets[0];
  const selectedDocumentPolishPreset =
    documentPolishPresets.find((preset) => preset.id === selectedDocumentPolishPresetId) ??
    documentPolishPresets[0];
  const selectedDocumentGenerationPreset =
    documentGenerationPresets.find(
      (preset) => preset.id === selectedDocumentGenerationPresetId,
    ) ?? documentGenerationPresets[0];
  const selectedEditorPreset =
    editorPresets.find((preset) => preset.id === selectedEditorPresetId) ?? editorPresets[0];

  useEffect(() => {
    if (!writingPresets.some((preset) => preset.id === selectedWritingPresetId)) {
      setSelectedWritingPresetId(writingPresets[0]?.id ?? "");
    }
    if (
      !quickGenerationPresets.some(
        (preset) => preset.id === selectedQuickGenerationPresetId,
      )
    ) {
      setSelectedQuickGenerationPresetId(quickGenerationPresets[0]?.id ?? "");
    }
    if (!authorPresets.some((preset) => preset.id === selectedAuthorPresetId)) {
      setSelectedAuthorPresetId(authorPresets[0]?.id ?? "");
    }
    if (
      !chapterBlueprintPresets.some(
        (preset) => preset.id === selectedChapterBlueprintPresetId,
      )
    ) {
      setSelectedChapterBlueprintPresetId(chapterBlueprintPresets[0]?.id ?? "");
    }
    if (!polishPresets.some((preset) => preset.id === selectedPolishPresetId)) {
      setSelectedPolishPresetId(polishPresets[0]?.id ?? "");
    }
    if (
      !documentPolishPresets.some((preset) => preset.id === selectedDocumentPolishPresetId)
    ) {
      setSelectedDocumentPolishPresetId(documentPolishPresets[0]?.id ?? "");
    }
    if (
      !documentGenerationPresets.some(
        (preset) => preset.id === selectedDocumentGenerationPresetId,
      )
    ) {
      setSelectedDocumentGenerationPresetId(documentGenerationPresets[0]?.id ?? "");
    }
    if (!editorPresets.some((preset) => preset.id === selectedEditorPresetId)) {
      setSelectedEditorPresetId(editorPresets[0]?.id ?? "");
    }
  }, [
    authorPresets,
    chapterBlueprintPresets,
    documentGenerationPresets,
    documentPolishPresets,
    editorPresets,
    polishPresets,
    quickGenerationPresets,
    selectedAuthorPresetId,
    selectedChapterBlueprintPresetId,
    selectedDocumentGenerationPresetId,
    selectedDocumentPolishPresetId,
    selectedEditorPresetId,
    selectedPolishPresetId,
    selectedQuickGenerationPresetId,
    selectedWritingPresetId,
    writingPresets,
  ]);

  function selectGenerationPreset(kind: GenerationPresetKind, presetId: string) {
    if (kind === "writing_mode") {
      setSelectedWritingPresetId(presetId);
    } else if (kind === "quick_generation_mode") {
      setSelectedQuickGenerationPresetId(presetId);
    } else if (kind === "chapter_blueprint_mode") {
      setSelectedChapterBlueprintPresetId(presetId);
    } else if (kind === "author_persona") {
      setSelectedAuthorPresetId(presetId);
    } else if (kind === "polish_mode") {
      setSelectedPolishPresetId(presetId);
    } else if (kind === "document_polish_mode") {
      setSelectedDocumentPolishPresetId(presetId);
    } else if (kind === "document_generation_mode") {
      setSelectedDocumentGenerationPresetId(presetId);
    } else {
      setSelectedEditorPresetId(presetId);
    }
  }

  return {
    selectedAuthorPreset,
    selectedAuthorPresetId,
    selectedChapterBlueprintPreset,
    selectedChapterBlueprintPresetId,
    selectedDocumentGenerationPreset,
    selectedDocumentGenerationPresetId,
    selectedDocumentPolishPreset,
    selectedDocumentPolishPresetId,
    selectedEditorPreset,
    selectedEditorPresetId,
    selectedPolishPreset,
    selectedPolishPresetId,
    selectedQuickGenerationPreset,
    selectedQuickGenerationPresetId,
    selectedWritingPreset,
    selectedWritingPresetId,
    selectGenerationPreset,
    setSelectedAuthorPresetId,
    setSelectedChapterBlueprintPresetId,
    setSelectedDocumentGenerationPresetId,
    setSelectedDocumentPolishPresetId,
    setSelectedEditorPresetId,
    setSelectedPolishPresetId,
    setSelectedQuickGenerationPresetId,
    setSelectedWritingPresetId,
  };
}
