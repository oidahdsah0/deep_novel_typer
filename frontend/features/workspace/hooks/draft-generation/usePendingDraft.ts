"use client";

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useState } from "react";
import type {
  ActiveResource,
  ChapterSelection,
  FloatingMenuPosition,
  PendingDraftGenerationState,
} from "../../types";

export function usePendingDraft({
  commitGeneratedContent,
  resource,
  setChapterSelection,
  setContent,
  setSelectionMenuPosition,
}: {
  commitGeneratedContent: (nextContent: string) => void;
  resource: ActiveResource;
  setChapterSelection: Dispatch<SetStateAction<ChapterSelection | null>>;
  setContent: Dispatch<SetStateAction<string>>;
  setSelectionMenuPosition: Dispatch<SetStateAction<FloatingMenuPosition>>;
}) {
  const [pendingDraftGeneration, setPendingDraftGeneration] =
    useState<PendingDraftGenerationState | null>(null);

  useEffect(() => {
    setPendingDraftGeneration((current) => {
      if (!current || (resource.type === "chapter" && current.chapterId === resource.id)) {
        return current;
      }
      return null;
    });
  }, [resource.id, resource.type]);

  function hideSelectionMenu() {
    setChapterSelection(null);
    setSelectionMenuPosition((current) =>
      current.visible ? { ...current, visible: false } : current,
    );
  }

  function acceptPendingDraft() {
    if (pendingDraftGeneration?.status !== "ready") {
      return false;
    }
    const nextContent = pendingDraftGeneration.nextContent;
    setPendingDraftGeneration(null);
    hideSelectionMenu();
    commitGeneratedContent(nextContent);
    return true;
  }

  function discardPendingDraft() {
    if (pendingDraftGeneration?.status === "ready") {
      setContent(pendingDraftGeneration.baseContent);
      setPendingDraftGeneration(null);
      hideSelectionMenu();
      return true;
    }
    if (pendingDraftGeneration?.status === "error") {
      setPendingDraftGeneration(null);
      return true;
    }
    return false;
  }

  return {
    acceptPendingDraft,
    discardPendingDraft,
    pendingDraftGeneration,
    setPendingDraftGeneration,
  };
}
