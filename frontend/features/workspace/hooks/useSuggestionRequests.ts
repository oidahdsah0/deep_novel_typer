"use client";

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useRef, useState } from "react";
import {
  requestSuggestions,
  type SuggestionRequestTrigger,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import { shouldApplySuggestionResponse } from "@/features/workspace/suggestionRequestGuards";
import type { SuggestionRequestsApi } from "./workspaceInteractionApiTypes";

export type { SuggestionRequestsApi } from "./workspaceInteractionApiTypes";

const autoSuggestionStorageKeyPrefix = "deep-novel-typer:auto-suggestions";

function uniqueIds(ids: string[]) {
  return Array.from(new Set(ids.filter(Boolean)));
}

export function useSuggestionRequests({
  activeChapterId,
  activeParagraph,
  projectId,
  setWorkspace,
}: {
  activeChapterId: string;
  activeParagraph: string;
  projectId: string;
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
}) {
  const pendingCountsRef = useRef<Map<string, number>>(new Map());
  const activeChapterIdRef = useRef(activeChapterId);
  const activeParagraphRef = useRef(activeParagraph);
  const latestAutoParagraphRef = useRef<Map<string, string>>(new Map());
  const [isSuggestionAutoEnabled, setSuggestionAutoEnabledState] = useState(false);
  const [pendingRequestKeys, setPendingRequestKeys] = useState<string[]>([]);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);
  const storageKey = `${autoSuggestionStorageKeyPrefix}:${projectId}`;

  useEffect(() => {
    activeChapterIdRef.current = activeChapterId;
    setSuggestionError(null);
  }, [activeChapterId]);

  useEffect(() => {
    activeParagraphRef.current = activeParagraph;
  }, [activeParagraph]);

  useEffect(() => {
    pendingCountsRef.current.clear();
    latestAutoParagraphRef.current.clear();
    setPendingRequestKeys([]);
    setSuggestionError(null);
    setSuggestionAutoEnabledState(window.localStorage.getItem(storageKey) === "true");
  }, [storageKey]);

  const pendingPerspectiveIds = pendingRequestKeys
    .filter((key) => key.startsWith(`${activeChapterId}:`))
    .map((key) => key.slice(activeChapterId.length + 1));

  function setIsSuggestionAutoEnabled(nextValue: SetStateAction<boolean>) {
    setSuggestionAutoEnabledState((current) => {
      const value = typeof nextValue === "function" ? nextValue(current) : nextValue;
      window.localStorage.setItem(storageKey, value ? "true" : "false");
      return value;
    });
  }

  function requestKey(chapterId: string, perspectiveId: string) {
    return `${chapterId}:${perspectiveId}`;
  }

  function isPending(chapterId: string, perspectiveId: string) {
    return (pendingCountsRef.current.get(requestKey(chapterId, perspectiveId)) ?? 0) > 0;
  }

  function markPending(chapterId: string, perspectiveId: string) {
    const key = requestKey(chapterId, perspectiveId);
    pendingCountsRef.current.set(key, (pendingCountsRef.current.get(key) ?? 0) + 1);
    setPendingRequestKeys((current) =>
      current.includes(key) ? current : [...current, key],
    );
  }

  function clearPending(chapterId: string, perspectiveId: string) {
    const key = requestKey(chapterId, perspectiveId);
    const nextCount = (pendingCountsRef.current.get(key) ?? 0) - 1;
    if (nextCount > 0) {
      pendingCountsRef.current.set(key, nextCount);
      return;
    }

    pendingCountsRef.current.delete(key);
    setPendingRequestKeys((current) => current.filter((item) => item !== key));
  }

  function replacePerspectiveSuggestions(
    chapterId: string,
    perspectiveId: string,
    suggestions: WorkspaceSnapshot["suggestions"],
  ) {
    setWorkspace((current) => {
      if (current.active_chapter.id !== chapterId) {
        return current;
      }

      return {
        ...current,
        suggestions: [
          ...current.suggestions.filter((suggestion) => suggestion.perspective_id !== perspectiveId),
          ...suggestions,
        ],
      };
    });
  }

  function requestPerspectiveSuggestion(
    chapterId: string,
    paragraph: string,
    perspectiveId: string,
    trigger: SuggestionRequestTrigger = "manual",
  ) {
    const normalizedParagraph = paragraph.trim();
    if (!normalizedParagraph) {
      if (trigger !== "auto") {
        setSuggestionError("当前章节还没有可用于视角建议的正文段落。");
      }
      return;
    }
    if (!perspectiveId || (trigger !== "auto" && isPending(chapterId, perspectiveId))) {
      return;
    }

    const key = requestKey(chapterId, perspectiveId);
    if (trigger === "auto") {
      latestAutoParagraphRef.current.set(key, normalizedParagraph);
    }
    markPending(chapterId, perspectiveId);
    setSuggestionError(null);
    void requestSuggestions(projectId, chapterId, normalizedParagraph, perspectiveId, trigger)
      .then((suggestions) => {
        if (!shouldApplySuggestionResponse({
          currentParagraph: activeParagraphRef.current,
          latestAutoParagraph: latestAutoParagraphRef.current.get(key),
          requestedParagraph: normalizedParagraph,
          trigger,
        })) {
          return;
        }
        if (trigger === "auto" && suggestions.length === 0) {
          return;
        }
        replacePerspectiveSuggestions(chapterId, perspectiveId, suggestions);
      })
      .catch(() => {
        if (
          activeChapterIdRef.current === chapterId &&
          shouldApplySuggestionResponse({
            currentParagraph: activeParagraphRef.current,
            latestAutoParagraph: latestAutoParagraphRef.current.get(key),
            requestedParagraph: normalizedParagraph,
            trigger,
          })
        ) {
          setSuggestionError("建议请求失败，可稍后重试。");
        }
      })
      .finally(() => {
        clearPending(chapterId, perspectiveId);
      });
  }

  function requestEnabledPerspectiveSuggestions(
    chapterId: string,
    paragraph: string,
    perspectiveIds: string[],
    trigger: SuggestionRequestTrigger = "batch",
  ) {
    const normalizedIds = uniqueIds(perspectiveIds);
    if (!paragraph.trim()) {
      if (trigger !== "auto") {
        setSuggestionError("当前章节还没有可用于视角建议的正文段落。");
      }
      return;
    }
    if (normalizedIds.length === 0) {
      if (trigger !== "auto") {
        setSuggestionError("没有开启的视角可批量刷新。");
      }
      return;
    }

    setSuggestionError(null);
    normalizedIds.forEach((perspectiveId) => {
      requestPerspectiveSuggestion(chapterId, paragraph, perspectiveId, trigger);
    });
  }

  return {
    isBatchSuggestionPending: pendingPerspectiveIds.length > 0,
    isSuggestionAutoEnabled,
    pendingPerspectiveIds,
    requestEnabledPerspectiveSuggestions,
    requestPerspectiveSuggestion,
    setIsSuggestionAutoEnabled,
    suggestionError,
  } satisfies SuggestionRequestsApi;
}
