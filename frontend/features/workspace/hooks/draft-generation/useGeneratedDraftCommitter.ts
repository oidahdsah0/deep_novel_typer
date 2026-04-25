"use client";

import { useEffect, useRef } from "react";
import type { Dispatch, SetStateAction } from "react";
import type { GeneratedDraft } from "@/lib/api/index";
import { insertGeneratedTextWithRange } from "../../utils";
import type {
  ActiveResource,
  PendingDraftGenerationAction,
  PendingDraftGenerationState,
} from "../../types";
import { generationErrorMessage } from "./draftGenerationErrors";

export function useGeneratedDraftCommitter({
  commitGeneratedContent,
  resource,
  setContent,
  setPendingDraftGeneration,
}: {
  commitGeneratedContent: (nextContent: string) => void;
  resource: ActiveResource;
  setContent: Dispatch<SetStateAction<string>>;
  setPendingDraftGeneration: Dispatch<SetStateAction<PendingDraftGenerationState | null>>;
}) {
  const resourceRef = useRef<ActiveResource>(resource);

  useEffect(() => {
    resourceRef.current = resource;
  }, [resource]);

  function commitGeneratedDraft({
    action,
    baseContent,
    chapterId,
    cursorIndex,
    result,
  }: {
    action: PendingDraftGenerationAction;
    baseContent: string;
    chapterId: string;
    cursorIndex: number;
    result: GeneratedDraft;
  }) {
    const inserted = insertGeneratedTextWithRange(baseContent, result.text, cursorIndex);
    if (!inserted) {
      throw new Error("模型没有返回可插入的正文。");
    }
    const latestResource = resourceRef.current;
    if (latestResource.type !== "chapter" || latestResource.id !== chapterId) {
      return;
    }
    if (action === "quick_next_paragraph") {
      setPendingDraftGeneration(null);
      commitGeneratedContent(inserted.nextContent);
      return;
    }
    setContent(inserted.nextContent);
    setPendingDraftGeneration({
      action,
      baseContent,
      chapterId,
      end: inserted.end,
      model: result.model,
      nextContent: inserted.nextContent,
      source: result.source,
      start: inserted.start,
      status: "ready",
      text: result.text.trim(),
    });
  }

  function setDraftError({
    action,
    chapterId,
    error,
  }: {
    action: PendingDraftGenerationAction;
    chapterId: string;
    error: unknown;
  }) {
    const latestResource = resourceRef.current;
    if (latestResource.type === "chapter" && latestResource.id === chapterId) {
      setPendingDraftGeneration({
        action,
        chapterId,
        error: generationErrorMessage(error),
        status: "error",
      });
    }
  }

  return { commitGeneratedDraft, setDraftError };
}
