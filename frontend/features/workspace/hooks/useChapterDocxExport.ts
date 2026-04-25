"use client";

import { useState } from "react";
import {
  exportChaptersDocx,
  type ChapterSummary,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import {
  chapterDocxDownloadFilename,
  downloadBlob,
  errorMessage,
} from "@/features/workspace/workspaceClientUtils";
import type {
  ChapterDocxExportApi,
  ChapterDocxExportDialogState,
} from "./workspaceInteractionApiTypes";

export type {
  ChapterDocxExportApi,
  ChapterDocxExportDialogState,
} from "./workspaceInteractionApiTypes";

type UseChapterDocxExportOptions = {
  content: string;
  projectId: string;
  saveActive: (
    nextContent?: string,
    options?: { throwOnError?: boolean },
  ) => Promise<void>;
  workspace: WorkspaceSnapshot;
};

export function useChapterDocxExport({
  content,
  projectId,
  saveActive,
  workspace,
}: UseChapterDocxExportOptions) {
  const [docxExportDialog, setDocxExportDialog] =
    useState<ChapterDocxExportDialogState>(null);

  function handleOpenChapterDocxExportDialog() {
    setDocxExportDialog({
      selectedChapterIds: workspace.chapters.map((chapter) => chapter.id),
      isExporting: false,
      error: null,
    });
  }

  function handleToggleDocxExportChapter(chapterId: string) {
    setDocxExportDialog((current) => {
      if (!current || current.isExporting) {
        return current;
      }
      const selected = new Set(current.selectedChapterIds);
      if (selected.has(chapterId)) {
        selected.delete(chapterId);
      } else {
        selected.add(chapterId);
      }
      const selectedChapterIds = workspace.chapters
        .map((chapter) => chapter.id)
        .filter((id) => selected.has(id));
      return { ...current, selectedChapterIds, error: null };
    });
  }

  function handleSelectAllDocxExportChapters() {
    setDocxExportDialog((current) =>
      current && !current.isExporting
        ? {
            ...current,
            selectedChapterIds: workspace.chapters.map((chapter) => chapter.id),
            error: null,
          }
        : current,
    );
  }

  function handleClearDocxExportChapters() {
    setDocxExportDialog((current) =>
      current && !current.isExporting
        ? { ...current, selectedChapterIds: [], error: null }
        : current,
    );
  }

  async function handleExportSelectedChaptersDocx() {
    const dialog = docxExportDialog;
    if (!dialog || dialog.isExporting || !dialog.selectedChapterIds.length) {
      return;
    }

    setDocxExportDialog({ ...dialog, isExporting: true, error: null });
    try {
      await saveActive(content, { throwOnError: true });
      const blob = await exportChaptersDocx(projectId, {
        chapter_ids: dialog.selectedChapterIds,
      });
      downloadBlob(
        blob,
        chapterDocxDownloadFilename(
          workspace.project.title,
          workspace.chapters as ChapterSummary[],
          dialog.selectedChapterIds,
        ),
      );
      setDocxExportDialog(null);
    } catch (error) {
      setDocxExportDialog((current) =>
        current
          ? {
              ...current,
              isExporting: false,
              error: errorMessage(error, "正文 DOCX 导出失败"),
            }
          : current,
      );
    }
  }

  return {
    docxExportDialog,
    handleClearDocxExportChapters,
    handleExportSelectedChaptersDocx,
    handleOpenChapterDocxExportDialog,
    handleSelectAllDocxExportChapters,
    handleToggleDocxExportChapter,
    setDocxExportDialog,
  } satisfies ChapterDocxExportApi;
}
