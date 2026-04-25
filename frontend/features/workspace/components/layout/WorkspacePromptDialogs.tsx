"use client";

import { ChapterDocxExportDialog } from "@/features/workspace/components/chapters/ChapterDocxExportDialog";
import { PromptManagerDialog } from "@/features/workspace/components/prompts/PromptManagerDialog";
import { PromptPreviewDialog } from "@/features/workspace/components/prompts/PromptPreviewDialog";
import { PromptProfileVersionDialog } from "@/features/workspace/components/prompts/PromptProfileVersionDialog";
import type { ChapterDocxExportApi } from "@/features/workspace/hooks/useChapterDocxExport";
import type { PromptPreviewApi } from "@/features/workspace/hooks/usePromptPreview";
import type { PromptProfilesApi } from "@/features/workspace/hooks/usePromptProfiles";
import type { PromptMaterialOption } from "@/features/workspace/types";
import type { ApiConfig, ChapterSummary } from "@/lib/api/index";

type WorkspacePromptDialogsProps = {
  apiConfigs: ApiConfig[];
  chapters: ChapterSummary[];
  docxExport: ChapterDocxExportApi;
  promptChapterOptions: PromptMaterialOption[];
  promptDocumentOptions: PromptMaterialOption[];
  promptPreview: PromptPreviewApi;
  promptProfiles: PromptProfilesApi;
};

export function WorkspacePromptDialogs({
  apiConfigs,
  chapters,
  docxExport,
  promptChapterOptions,
  promptDocumentOptions,
  promptPreview,
  promptProfiles,
}: WorkspacePromptDialogsProps) {
  const docxDialog = docxExport.docxExportDialog;
  return (
    <>
      {docxDialog ? (
        <ChapterDocxExportDialog
          chapters={chapters}
          error={docxDialog.error}
          isExporting={docxDialog.isExporting}
          onClear={docxExport.handleClearDocxExportChapters}
          onClose={() => docxExport.setDocxExportDialog(null)}
          onExport={() => void docxExport.handleExportSelectedChaptersDocx()}
          onSelectAll={docxExport.handleSelectAllDocxExportChapters}
          onToggleChapter={docxExport.handleToggleDocxExportChapter}
          selectedChapterIds={docxDialog.selectedChapterIds}
        />
      ) : null}
      {promptProfiles.isPromptManagerOpen && promptProfiles.promptDraft ? (
        <PromptManagerDialog
          activeRequestType={promptProfiles.activePromptRequestType}
          apiConfigs={apiConfigs}
          chapterOptions={promptChapterOptions}
          documentOptions={promptDocumentOptions}
          draft={promptProfiles.promptDraft}
          isPreviewing={promptPreview.isPromptPreviewLoading}
          onChangeDraft={promptProfiles.patchPromptDraft}
          onClose={() => promptProfiles.setIsPromptManagerOpen(false)}
          onOpenHistory={promptProfiles.handleOpenPromptVersions}
          onPreview={promptPreview.handlePreviewPromptManager}
          onSave={() => void promptProfiles.handleSavePromptProfile()}
          onSelectRequestType={promptProfiles.handleSelectPromptRequestType}
          onToggleChapter={promptProfiles.togglePromptChapter}
          onToggleDocument={promptProfiles.togglePromptDocument}
          saveState={promptProfiles.promptSaveState}
        />
      ) : null}
      {promptProfiles.isPromptVersionDialogOpen ? (
        <PromptProfileVersionDialog
          isLoading={promptProfiles.isPromptVersionLoading}
          onClose={() => promptProfiles.setIsPromptVersionDialogOpen(false)}
          onRestore={(version) => void promptProfiles.handleRestorePromptProfileVersion(version)}
          onSelectVersion={(version) => void promptProfiles.handleSelectPromptVersion(version)}
          requestType={promptProfiles.activePromptRequestType}
          selectedVersion={promptProfiles.selectedPromptVersion}
          versions={promptProfiles.promptVersions}
        />
      ) : null}
      {promptPreview.promptPreview ? (
        <PromptPreviewDialog
          preview={promptPreview.promptPreview}
          onClose={() => promptPreview.setPromptPreview(null)}
        />
      ) : null}
    </>
  );
}
