"use client";

import { ChapterBlueprintDialog } from "@/features/workspace/components/generation/ChapterBlueprintDialog";
import { DocumentGenerationDialog } from "@/features/workspace/components/generation/DocumentGenerationDialog";
import { GenerationDialog } from "@/features/workspace/components/generation/GenerationDialog";
import { PolishDialog } from "@/features/workspace/components/generation/PolishDialog";
import type { DocumentGenerationApi } from "@/features/workspace/hooks/useDocumentGeneration";
import type { DraftGenerationApi } from "@/features/workspace/hooks/useDraftGeneration";
import type { GenerationPresetsApi } from "@/features/workspace/hooks/useGenerationPresets";
import type { PromptPreviewApi } from "@/features/workspace/hooks/usePromptPreview";
import type { ChapterSelection } from "@/features/workspace/types";

type WorkspaceGenerationDialogsProps = {
  documentGeneration: DocumentGenerationApi;
  draftGeneration: DraftGenerationApi;
  generationPresets: GenerationPresetsApi;
  promptPreview: PromptPreviewApi;
  chapterSelection: ChapterSelection | null;
  documentSelection: ChapterSelection | null;
};

export function WorkspaceGenerationDialogs({
  documentGeneration,
  draftGeneration,
  generationPresets,
  promptPreview,
  chapterSelection,
  documentSelection,
}: WorkspaceGenerationDialogsProps) {
  const generationDialog = draftGeneration.generationDialog;
  const blueprintDialog = draftGeneration.chapterBlueprintDialog;
  const polishDialog = draftGeneration.polishDialog;
  const documentDialog = documentGeneration.documentGenerationDialog;

  return (
    <>
      {generationDialog ? (
        <GenerationDialog
          action={generationDialog.action}
          authorPresets={generationPresets.authorPresets}
          authorPreset={generationPresets.selectedAuthorPreset}
          error={generationDialog.error}
          isGenerating={draftGeneration.isGeneratingDraft}
          isPreviewing={promptPreview.isPromptPreviewLoading}
          onAccept={draftGeneration.handleAcceptDraft}
          onAddPreset={generationPresets.handleCreateGenerationPreset}
          onChangeAuthorPreset={generationPresets.setSelectedAuthorPresetId}
          onChangePresetContent={generationPresets.handlePresetContentChange}
          onChangeWritingPreset={generationPresets.setSelectedWritingPresetId}
          onClose={() => draftGeneration.setGenerationDialog(null)}
          onDeletePreset={generationPresets.handleDeleteGenerationPreset}
          onDiscard={draftGeneration.handleDiscardDraft}
          onGenerate={() => void draftGeneration.handleGenerateDraft()}
          onPreview={() =>
            void promptPreview.handlePreviewDraftGeneration(
              generationDialog.action,
              generationDialog.anchor,
            )
          }
          onRenamePreset={generationPresets.handleRenameGenerationPreset}
          presetSaveState={generationPresets.presetSaveState}
          result={generationDialog.result}
          selectedAuthorPresetId={generationPresets.selectedAuthorPresetId}
          selectedWritingPresetId={generationPresets.selectedWritingPresetId}
          writingPreset={generationPresets.selectedWritingPreset}
          writingPresets={generationPresets.writingPresets}
        />
      ) : null}
      {blueprintDialog ? (
        <ChapterBlueprintDialog
          authorPresets={generationPresets.authorPresets}
          authorPreset={generationPresets.selectedAuthorPreset}
          blueprintPreset={generationPresets.selectedChapterBlueprintPreset}
          blueprintPresets={generationPresets.chapterBlueprintPresets}
          error={blueprintDialog.error}
          isGenerating={draftGeneration.isGeneratingChapterBlueprint}
          isPreviewing={promptPreview.isPromptPreviewLoading}
          onAccept={draftGeneration.handleAcceptChapterBlueprint}
          onAddPreset={generationPresets.handleCreateGenerationPreset}
          onChangeAuthorPreset={generationPresets.setSelectedAuthorPresetId}
          onChangeBlueprintPreset={generationPresets.setSelectedChapterBlueprintPresetId}
          onChangePresetContent={generationPresets.handlePresetContentChange}
          onClose={() => draftGeneration.setChapterBlueprintDialog(null)}
          onDeletePreset={generationPresets.handleDeleteGenerationPreset}
          onDiscard={draftGeneration.handleDiscardChapterBlueprint}
          onGenerate={() => void draftGeneration.handleGenerateChapterBlueprint()}
          onPreview={() => void promptPreview.handlePreviewPrompt("generate_chapter_blueprint")}
          onRenamePreset={generationPresets.handleRenameGenerationPreset}
          presetSaveState={generationPresets.presetSaveState}
          result={blueprintDialog.result}
          selectedAuthorPresetId={generationPresets.selectedAuthorPresetId}
          selectedBlueprintPresetId={generationPresets.selectedChapterBlueprintPresetId}
        />
      ) : null}
      {polishDialog ? (
        <PolishDialog
          error={polishDialog.error}
          isGenerating={draftGeneration.isPolishing}
          isPreviewing={promptPreview.isPromptPreviewLoading}
          onAccept={draftGeneration.handleAcceptPolish}
          onAddPreset={generationPresets.handleCreateGenerationPreset}
          onChangePolishPreset={generationPresets.setSelectedPolishPresetId}
          onChangePresetContent={generationPresets.handlePresetContentChange}
          onClose={() => draftGeneration.setPolishDialog(null)}
          onDeletePreset={generationPresets.handleDeleteGenerationPreset}
          onDiscard={draftGeneration.handleDiscardPolish}
          onGenerate={() => void draftGeneration.handleGeneratePolish()}
          onPreview={() => void promptPreview.handlePreviewPrompt("polish_selection")}
          onRenamePreset={generationPresets.handleRenameGenerationPreset}
          polishPreset={generationPresets.selectedPolishPreset}
          polishPresets={generationPresets.polishPresets}
          presetSaveState={generationPresets.presetSaveState}
          result={polishDialog.result}
          selectedPolishPresetId={generationPresets.selectedPolishPresetId}
          selectedText={chapterSelection?.text ?? ""}
        />
      ) : null}
      {documentDialog ? (
        <DocumentGenerationDialog
          action={documentDialog.action}
          documentGenerationPreset={generationPresets.selectedDocumentGenerationPreset}
          documentGenerationPresets={generationPresets.documentGenerationPresets}
          documentPolishPreset={generationPresets.selectedDocumentPolishPreset}
          documentPolishPresets={generationPresets.documentPolishPresets}
          editorPreset={generationPresets.selectedEditorPreset}
          editorPresets={generationPresets.editorPresets}
          error={documentDialog.error}
          isGenerating={documentGeneration.isGeneratingDocument}
          isPreviewing={promptPreview.isPromptPreviewLoading}
          onAccept={documentGeneration.handleAcceptDocumentGeneration}
          onAddPreset={generationPresets.handleCreateGenerationPreset}
          onChangeDocumentGenerationPreset={generationPresets.setSelectedDocumentGenerationPresetId}
          onChangeDocumentPolishPreset={generationPresets.setSelectedDocumentPolishPresetId}
          onChangeEditorPreset={generationPresets.setSelectedEditorPresetId}
          onChangePresetContent={generationPresets.handlePresetContentChange}
          onClose={() => documentGeneration.setDocumentGenerationDialog(null)}
          onDeletePreset={generationPresets.handleDeleteGenerationPreset}
          onDiscard={documentGeneration.handleDiscardDocumentGeneration}
          onGenerate={() => void documentGeneration.handleGenerateDocument()}
          onPreview={() =>
            void promptPreview.handlePreviewPrompt(
              documentDialog.action === "polish_selection"
                ? "polish_document_selection"
                : "generate_document_continuation",
            )
          }
          onRenamePreset={generationPresets.handleRenameGenerationPreset}
          presetSaveState={generationPresets.presetSaveState}
          result={documentDialog.result}
          selectedDocumentGenerationPresetId={generationPresets.selectedDocumentGenerationPresetId}
          selectedDocumentPolishPresetId={generationPresets.selectedDocumentPolishPresetId}
          selectedEditorPresetId={generationPresets.selectedEditorPresetId}
          selectedText={documentSelection?.text ?? ""}
        />
      ) : null}
    </>
  );
}
