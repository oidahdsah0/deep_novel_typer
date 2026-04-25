"use client";

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useLayoutEffect, useState } from "react";
import type {
  ActiveResource,
  ChapterSelection,
  MarkdownViewMode,
} from "@/features/workspace/types";
import { useWritingMenuPositions } from "@/features/workspace/hooks/useWritingMenuPositions";
import { draftInsertionContextAt } from "@/features/workspace/utils";
import type { WorkspaceEditorApi } from "./workspaceInteractionApiTypes";

export type { WorkspaceEditorApi } from "./workspaceInteractionApiTypes";

type UseWorkspaceEditorInteractionsOptions = {
  content: string;
  setContent: Dispatch<SetStateAction<string>>;
  resource: ActiveResource;
};

export function useWorkspaceEditorInteractions({
  content,
  setContent,
  resource,
}: UseWorkspaceEditorInteractionsOptions) {
  const [markdownViewMode, setMarkdownViewMode] = useState<MarkdownViewMode>("split");
  const [chapterSelection, setChapterSelection] = useState<ChapterSelection | null>(null);
  const [documentSelection, setDocumentSelection] = useState<ChapterSelection | null>(null);
  const activeSelection = resource.type === "chapter" ? chapterSelection : documentSelection;
  const {
    draftMenuPosition,
    hideSelectionMenu,
    hideWritingCaret,
    selectionMenuPosition,
    setSelectionMenuPosition,
    updateDraftMenuPosition,
    updateSelectionMenuPosition,
    updateWritingCaretPosition,
    writingCaretPosition,
    writingMirrorRef,
    writingSurfaceRef,
  } = useWritingMenuPositions({
    chapterSelection,
    resourceType: resource.type,
  });

  function readChapterSelection(): ChapterSelection | null {
    const textarea = writingSurfaceRef.current;
    if (resource.type !== "chapter" || !textarea) {
      return null;
    }
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    if (end <= start) {
      return null;
    }
    const text = textarea.value.slice(start, end);
    return text.trim() ? { start, end, text } : null;
  }

  function readDraftInsertionContext() {
    const textarea = writingSurfaceRef.current;
    const cursorIndex =
      resource.type === "chapter" && textarea ? textarea.selectionEnd : content.length;
    return draftInsertionContextAt(content, cursorIndex);
  }

  function handleChapterSelectionChange() {
    const nextSelection = readChapterSelection();
    setChapterSelection((current) =>
      current?.start === nextSelection?.start &&
      current?.end === nextSelection?.end &&
      current?.text === nextSelection?.text
        ? current
        : nextSelection,
    );
    updateSelectionMenuPosition(nextSelection);
    updateDraftMenuPosition();
    updateWritingCaretPosition();
  }

  function handleChapterContentChange(nextContent: string) {
    setContent(nextContent);
    setChapterSelection(null);
    hideSelectionMenu();
    window.requestAnimationFrame(updateDraftMenuPosition);
    window.requestAnimationFrame(updateWritingCaretPosition);
  }

  function handleDocumentContentChange(nextContent: string) {
    setContent(nextContent);
    setDocumentSelection(null);
  }

  function handleDocumentSelectionChange(nextSelection: ChapterSelection | null) {
    setDocumentSelection((current) =>
      current?.start === nextSelection?.start &&
      current?.end === nextSelection?.end &&
      current?.text === nextSelection?.text
        ? current
        : nextSelection,
    );
  }

  function handleWritingScroll() {
    updateDraftMenuPosition();
    updateSelectionMenuPosition();
    updateWritingCaretPosition();
  }

  function handleWritingBlur() {
    hideWritingCaret();
  }

  function handlePolishAcceptedSelection(start: number, end: number) {
    window.setTimeout(() => {
      const textarea = writingSurfaceRef.current;
      if (!textarea) {
        return;
      }
      textarea.focus();
      textarea.setSelectionRange(start, end);
      updateWritingCaretPosition();
    }, 0);
  }

  useEffect(() => {
    setChapterSelection(null);
    setDocumentSelection(null);
    hideSelectionMenu();
    hideWritingCaret();
  }, [hideSelectionMenu, hideWritingCaret, resource.id, resource.type]);

  useLayoutEffect(() => {
    updateDraftMenuPosition();
    updateSelectionMenuPosition();
    updateWritingCaretPosition();
  }, [
    content,
    resource.type,
    resource.id,
    updateDraftMenuPosition,
    updateSelectionMenuPosition,
    updateWritingCaretPosition,
  ]);

  useEffect(() => {
    function handleWindowResize() {
      updateDraftMenuPosition();
      updateSelectionMenuPosition();
      updateWritingCaretPosition();
    }

    window.addEventListener("resize", handleWindowResize);
    return () => window.removeEventListener("resize", handleWindowResize);
  }, [updateDraftMenuPosition, updateSelectionMenuPosition, updateWritingCaretPosition]);

  return {
    activeSelection,
    chapterSelection,
    documentSelection,
    draftMenuPosition,
    handleChapterContentChange,
    handleChapterSelectionChange,
    handleDocumentContentChange,
    handleDocumentSelectionChange,
    handlePolishAcceptedSelection,
    handleWritingBlur,
    handleWritingScroll,
    markdownViewMode,
    readChapterSelection,
    readDraftInsertionContext,
    selectionMenuPosition,
    setChapterSelection,
    setDocumentSelection,
    setMarkdownViewMode,
    setSelectionMenuPosition,
    updateDraftMenuPosition,
    updateSelectionMenuPosition,
    writingCaretPosition,
    writingMirrorRef,
    writingSurfaceRef,
  } satisfies WorkspaceEditorApi;
}
