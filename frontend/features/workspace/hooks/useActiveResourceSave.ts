"use client";

import type { Dispatch, SetStateAction } from "react";
import {
  saveChapter,
  saveDocument,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import {
  resourceUpdatedAt,
  saveFailureState,
} from "@/features/workspace/activeResourceSaveGuards";
import {
  getSaveQueue,
  syncIdleQueueBaseline,
  type SaveQueue,
} from "../activeResourceSaveQueue";
import { updateChapterNodeInTree, updateDocumentNodeInTree } from "@/features/workspace/treeUtils";
import type { ActiveResource, SaveState } from "@/features/workspace/types";
import { extractLastParagraph } from "@/features/workspace/workspaceClientUtils";

type SaveActiveOptions = { forceOverwrite?: boolean; throwOnError?: boolean };

type UseActiveResourceSaveOptions = {
  content: string;
  isSuggestionAutoEnabled: boolean;
  projectId: string;
  requestEnabledPerspectiveSuggestions: (
    chapterId: string,
    paragraph: string,
    perspectiveIds: string[],
    trigger?: "manual" | "batch" | "auto",
  ) => void;
  resource: ActiveResource;
  savedContent: string;
  setSavedContent: (savedContent: string) => void;
  setSaveState: Dispatch<SetStateAction<SaveState>>;
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
  workspace: WorkspaceSnapshot;
};

type SaveContext = UseActiveResourceSaveOptions & {
  resourceKey: string;
};

type SaveJob = {
  context: SaveContext;
  content: string;
  options: SaveActiveOptions;
  sequence: number;
  waiters: SaveWaiter[];
};

type SaveWaiter = {
  options: SaveActiveOptions;
  reject: (error: unknown) => void;
  resolve: () => void;
};

export function useActiveResourceSave({
  content,
  isSuggestionAutoEnabled,
  projectId,
  requestEnabledPerspectiveSuggestions,
  resource,
  savedContent,
  setSavedContent,
  setSaveState,
  setWorkspace,
  workspace,
}: UseActiveResourceSaveOptions) {
  async function saveActive(
    nextContent = content,
    options: SaveActiveOptions = {},
  ) {
    const resourceKey = `${projectId}:${resource.type}:${resource.id}`;
    const queue = getSaveQueue<SaveJob>(resourceKey);
    syncIdleQueueBaseline(queue, {
      resource,
      savedContent,
      workspace,
    });
    if (
      !options.forceOverwrite &&
      (nextContent === savedContent || nextContent === queue.lastSavedContent)
    ) {
      return;
    }

    setSaveState("saving");
    return await enqueueSave(queue, {
      context: {
        content,
        isSuggestionAutoEnabled,
        projectId,
        requestEnabledPerspectiveSuggestions,
        resource,
        resourceKey,
        savedContent,
        setSavedContent,
        setSaveState,
        setWorkspace,
        workspace,
      },
      content: nextContent,
      options,
      sequence: ++queue.latestSequence,
      waiters: [],
    });
  }

  return saveActive;
}

async function enqueueSave(queue: SaveQueue<SaveJob>, job: SaveJob): Promise<void> {
  return await new Promise<void>((resolve, reject) => {
    queue.pending = {
      ...job,
      waiters: [
        ...(queue.pending?.waiters ?? []),
        { options: job.options, reject, resolve },
      ],
    };
    void drainSaveQueue(queue);
  });
}

async function drainSaveQueue(queue: SaveQueue<SaveJob>) {
  if (queue.isDraining) return;
  queue.isDraining = true;
  try {
    while (queue.pending) {
      const job = queue.pending;
      queue.pending = null;
      const isLatest = () => job.sequence === queue.latestSequence;
      try {
        await performSave(queue, job, isLatest);
        resolveWaiters(job);
      } catch (error) {
        if (isLatest()) {
          job.context.setSaveState(saveFailureState(error));
        }
        settleFailedWaiters(job, error);
      }
    }
  } finally {
    queue.isDraining = false;
  }
}

function resolveWaiters(job: SaveJob) {
  for (const waiter of job.waiters) {
    waiter.resolve();
  }
}

function settleFailedWaiters(job: SaveJob, error: unknown) {
  for (const waiter of job.waiters) {
    if (waiter.options.throwOnError) {
      waiter.reject(error);
    } else {
      waiter.resolve();
    }
  }
}

async function performSave(queue: SaveQueue<SaveJob>, job: SaveJob, isLatest: () => boolean) {
  const { context, content: nextContent } = job;
  const baseUpdatedAt = job.options.forceOverwrite
    ? null
    : queue.lastSavedUpdatedAt ?? resourceUpdatedAt(context);
  if (context.resource.type === "chapter") {
    const paragraphForSuggestion = extractLastParagraph(nextContent) || nextContent.trim();
    const enabledIds = context.workspace.perspectives
      .filter((perspective) => perspective.is_enabled)
      .map((perspective) => perspective.id);
    const chapter = await saveChapter(
      context.projectId,
      context.resource.id,
      nextContent,
      baseUpdatedAt,
    );
    queue.lastSavedContent = nextContent;
    queue.lastSavedUpdatedAt = chapter.updated_at;
    if (!isLatest()) return;
    context.setWorkspace((current) => ({
      ...current,
      active_chapter: {
        id: chapter.id,
        title: chapter.title,
        content: chapter.content,
        word_count: chapter.word_count,
        writing_synopsis: chapter.writing_synopsis,
        writing_synopsis_updated_at: chapter.writing_synopsis_updated_at,
        updated_at: chapter.updated_at,
      },
      chapters: current.chapters.map((item) =>
        item.id === chapter.id ? { ...item, word_count: chapter.word_count } : item,
      ),
      chapter_tree: updateChapterNodeInTree(current.chapter_tree, {
        chapter_id: chapter.id,
        word_count: chapter.word_count,
        updated_at: chapter.updated_at,
      }),
      project: {
        ...current.project,
        ...chapter.project,
      },
    }));
    if (context.isSuggestionAutoEnabled) {
      context.requestEnabledPerspectiveSuggestions(chapter.id, paragraphForSuggestion, enabledIds, "auto");
    }
  } else {
    const document = await saveDocument(
      context.projectId,
      context.resource.id,
      nextContent,
      baseUpdatedAt,
    );
    queue.lastSavedContent = nextContent;
    queue.lastSavedUpdatedAt = document.updated_at;
    if (!isLatest()) return;
    context.setWorkspace((current) => ({
      ...current,
      document_tree: updateDocumentNodeInTree(current.document_tree, {
        id: document.id,
        title: document.title,
        updated_at: document.updated_at,
      }),
      project: {
        ...current.project,
        ...document.project,
      },
    }));
  }
  context.setSavedContent(nextContent);
  context.setSaveState("saved");
}
