"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import {
  ApiFetchError,
  saveChapterWritingSynopsis,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import { updateChapterNodeInTree } from "@/features/workspace/treeUtils";
import type { SaveState } from "@/features/workspace/types";

const collapsedStorageKey = "deep-novel-typer:chapter-writing-synopsis-panel-collapsed";

function readInitialCollapsedState() {
  if (typeof window === "undefined") {
    return true;
  }
  const storedValue = window.localStorage.getItem(collapsedStorageKey);
  return storedValue === null ? true : storedValue === "1";
}

export type ChapterWritingSynopsisApi = {
  draft: string;
  flush: () => Promise<void>;
  isCollapsed: boolean;
  saveState: SaveState;
  setDraft: (value: string) => void;
  setIsCollapsed: (value: boolean) => void;
};

export function useChapterWritingSynopsis({
  projectId,
  setWorkspace,
  workspace,
}: {
  projectId: string;
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
  workspace: WorkspaceSnapshot;
}): ChapterWritingSynopsisApi {
  const activeChapter = workspace.active_chapter;
  const activeChapterId = activeChapter.id;
  const activeWritingSynopsis = activeChapter.writing_synopsis;
  const activeWritingSynopsisUpdatedAt = activeChapter.writing_synopsis_updated_at;
  const [draft, setDraftState] = useState(activeChapter.writing_synopsis);
  const [saved, setSaved] = useState(activeChapter.writing_synopsis);
  const [saveState, setSaveState] = useState<SaveState>("saved");
  const [isCollapsed, setIsCollapsedState] = useState(readInitialCollapsedState);
  const activeChapterIdRef = useRef(activeChapter.id);
  const draftRef = useRef(activeChapter.writing_synopsis);
  const savedRef = useRef(activeChapter.writing_synopsis);
  const updatedAtRef = useRef(activeChapter.writing_synopsis_updated_at);
  const saveChainRef = useRef<Promise<void>>(Promise.resolve());

  const resetFromActiveChapter = useCallback(
    (chapterId: string, synopsis: string, updatedAt: string) => {
      activeChapterIdRef.current = chapterId;
      draftRef.current = synopsis;
      savedRef.current = synopsis;
      updatedAtRef.current = updatedAt;
      setDraftState(synopsis);
      setSaved(synopsis);
      setSaveState("saved");
    },
    [],
  );

  useEffect(() => {
    window.localStorage.setItem(collapsedStorageKey, isCollapsed ? "1" : "0");
  }, [isCollapsed]);

  useEffect(() => {
    const isNextChapter = activeChapterIdRef.current !== activeChapterId;
    const isClean = draftRef.current === savedRef.current;
    if (!isNextChapter && !isClean) {
      return;
    }
    resetFromActiveChapter(
      activeChapterId,
      activeWritingSynopsis,
      activeWritingSynopsisUpdatedAt,
    );
  }, [
    activeChapterId,
    activeWritingSynopsis,
    activeWritingSynopsisUpdatedAt,
    resetFromActiveChapter,
  ]);

  const setDraft = useCallback((value: string) => {
    draftRef.current = value;
    setDraftState(value);
    setSaveState(value === savedRef.current ? "saved" : "idle");
  }, []);

  const setIsCollapsed = useCallback((value: boolean) => {
    setIsCollapsedState(value);
  }, []);

  const performSave = useCallback(async () => {
    const chapterId = activeChapterIdRef.current;
    const nextSynopsis = draftRef.current;
    if (nextSynopsis === savedRef.current) {
      setSaveState("saved");
      return;
    }

    setSaveState("saving");
    try {
      const chapter = await saveChapterWritingSynopsis(
        projectId,
        chapterId,
        nextSynopsis,
        updatedAtRef.current || null,
      );
      if (activeChapterIdRef.current === chapter.id) {
        savedRef.current = chapter.writing_synopsis;
        updatedAtRef.current = chapter.writing_synopsis_updated_at;
        setSaved(chapter.writing_synopsis);
        setSaveState(draftRef.current === nextSynopsis ? "saved" : "idle");
      }
      setWorkspace((current) => ({
        ...current,
        active_chapter:
          current.active_chapter.id === chapter.id
            ? {
                ...current.active_chapter,
                writing_synopsis: chapter.writing_synopsis,
                writing_synopsis_updated_at: chapter.writing_synopsis_updated_at,
              }
            : current.active_chapter,
        chapter_tree: updateChapterNodeInTree(current.chapter_tree, {
          chapter_id: chapter.id,
          updated_at: chapter.writing_synopsis_updated_at,
        }),
        project: {
          ...current.project,
          ...chapter.project,
        },
      }));
    } catch (error) {
      setSaveState(error instanceof ApiFetchError && error.status === 409 ? "conflict" : "error");
      throw error;
    }
  }, [projectId, setWorkspace]);

  const flush = useCallback(async () => {
    const run = saveChainRef.current.then(performSave);
    saveChainRef.current = run.catch(() => undefined);
    return await run;
  }, [performSave]);

  useEffect(() => {
    if (draft === saved || saveState === "conflict") {
      return;
    }
    const timer = window.setTimeout(() => {
      void flush().catch(() => undefined);
    }, 900);
    return () => window.clearTimeout(timer);
  }, [draft, flush, saveState, saved]);

  return {
    draft,
    flush,
    isCollapsed,
    saveState,
    setDraft,
    setIsCollapsed,
  };
}
