"use client";

import { useLayoutEffect } from "react";
import type { RefObject } from "react";
import type {
  PendingDraftGenerationState,
  WritingEditorHandle,
} from "@/features/workspace/types";
import { scrollTextareaIndexIntoView } from "@/features/workspace/workspaceClientUtils";

export function usePendingDraftFocus(
  textareaRef: RefObject<WritingEditorHandle | null>,
  pendingDraft: PendingDraftGenerationState | null,
) {
  useLayoutEffect(() => {
    if (pendingDraft?.status !== "generating" && pendingDraft?.status !== "ready") {
      return;
    }
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }

    if (pendingDraft.status === "generating") {
      textarea.focus();
      textarea.setSelectionRangeWithoutScroll(
        pendingDraft.cursorIndex,
        pendingDraft.cursorIndex,
      );
      scrollTextareaIndexIntoView(textarea, pendingDraft.cursorIndex);
      return;
    }

    textarea.focus();
    textarea.setSelectionRangeWithoutScroll(pendingDraft.start, pendingDraft.end);
    scrollTextareaIndexIntoView(textarea, pendingDraft.start);
  }, [pendingDraft, textareaRef]);
}
