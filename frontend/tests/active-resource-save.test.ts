import assert from "node:assert/strict";
import moduleBuiltin from "node:module";
import test from "node:test";

import type { SetStateAction } from "react";
import type { SaveState } from "../features/workspace/types";
import type { WorkspaceSnapshot } from "../lib/api/types";

type ChapterResponse = {
  content: string;
  id: string;
  project: {
    id: string;
    title: string;
    updated_at: string;
    word_count: number;
  };
  title: string;
  updated_at: string;
  word_count: number;
  writing_synopsis: string;
  writing_synopsis_updated_at: string;
};

type Deferred<T> = {
  promise: Promise<T>;
  reject: (error: Error) => void;
  resolve: (value: T) => void;
};

type ModuleWithLoad = typeof moduleBuiltin & {
  _load(request: string, parent: unknown, isMain: boolean): unknown;
};

test("older save responses do not overwrite newer saved content", async () => {
  const oldSave = deferred<ChapterResponse>();
  const newSave = deferred<ChapterResponse>();
  const saveCalls: Array<{ baseUpdatedAt: string | null | undefined; content: string }> = [];
  const moduleWithLoad = moduleBuiltin as unknown as ModuleWithLoad;
  const originalLoad = moduleWithLoad._load;
  moduleWithLoad._load = function patchedLoad(
    this: unknown,
    request: string,
    parent: unknown,
    isMain: boolean,
  ) {
    if (request === "@/lib/api/index") {
      return {
        ApiFetchError: class ApiFetchError extends Error {
          constructor(
            message: string,
            public readonly status: number,
          ) {
            super(message);
          }
        },
        saveChapter: (
          projectId: string,
          _chapterId: string,
          content: string,
          baseUpdatedAt?: string | null,
        ) => {
          saveCalls.push({ baseUpdatedAt, content });
          if (content === "old") return oldSave.promise;
          if (content === "new") return newSave.promise;
          if (content === "first") return Promise.resolve(chapterResponse("first", "old-time", projectId));
          if (content === "after-reload") {
            return Promise.resolve(chapterResponse("after-reload", "after-time", projectId));
          }
          if (content === "force") return Promise.resolve(chapterResponse("force", "force-time", projectId));
          throw new Error(`Unexpected content: ${content}`);
        },
        saveDocument: () => {
          throw new Error("saveDocument should not be called");
        },
      };
    }
    if (request === "@/features/workspace/treeUtils") {
      return {
        updateChapterNodeInTree: (tree: unknown) => tree,
        updateDocumentNodeInTree: (tree: unknown) => tree,
      };
    }
    if (request === "@/features/workspace/activeResourceSaveGuards") {
      return {
        resourceUpdatedAt: ({ workspace }: { workspace: WorkspaceSnapshot }) =>
          workspace.active_chapter.updated_at,
        saveFailureState: () => "error",
      };
    }
    if (request === "@/features/workspace/workspaceClientUtils") {
      return {
        extractLastParagraph: (content: string) => content,
      };
    }
    return originalLoad.call(this, request, parent, isMain);
  };

  try {
    const { useActiveResourceSave } = await import(
      "../features/workspace/hooks/useActiveResourceSave"
    );
    let savedContent = "initial";
    let saveState: SaveState = "saved";
    let workspace = workspaceSnapshot();
    const saveActive = useActiveResourceSave({
      content: "initial",
      isSuggestionAutoEnabled: false,
      projectId: "project-1",
      requestEnabledPerspectiveSuggestions: () => undefined,
      resource: { type: "chapter", id: "chapter-001", title: "Chapter" },
      savedContent,
      setSavedContent: (value: SetStateAction<string>) => {
        savedContent = typeof value === "function" ? value(savedContent) : value;
      },
      setSaveState: (value: SetStateAction<SaveState>) => {
        saveState = typeof value === "function" ? value(saveState) : value;
      },
      setWorkspace: (value: SetStateAction<WorkspaceSnapshot>) => {
        workspace = typeof value === "function" ? value(workspace) : value;
      },
      workspace,
    } as unknown as Parameters<typeof useActiveResourceSave>[0]);

    const first = saveActive("old");
    const second = saveActive("new");
    assert.deepEqual(saveCalls, [{ baseUpdatedAt: "initial-time", content: "old" }]);

    oldSave.resolve(chapterResponse("old", "old-time"));
    await first;
    assert.equal(savedContent, "initial");
    assert.equal(saveState, "saving");
    assert.deepEqual(saveCalls, [
      { baseUpdatedAt: "initial-time", content: "old" },
      { baseUpdatedAt: "old-time", content: "new" },
    ]);

    newSave.resolve(chapterResponse("new", "new-time"));
    await second;

    assert.equal(savedContent, "new");
    assert.equal(saveState, "saved");

    let reloadedSavedContent = "initial";
    let reloadedSaveState: SaveState = "saved";
    let reloadedWorkspace = workspaceSnapshot("project-2", "initial", "initial-time");
    const firstSave = useActiveResourceSave({
      content: "initial",
      isSuggestionAutoEnabled: false,
      projectId: "project-2",
      requestEnabledPerspectiveSuggestions: () => undefined,
      resource: { type: "chapter", id: "chapter-001", title: "Chapter" },
      savedContent: reloadedSavedContent,
      setSavedContent: (value: SetStateAction<string>) => {
        reloadedSavedContent = typeof value === "function" ? value(reloadedSavedContent) : value;
      },
      setSaveState: (value: SetStateAction<SaveState>) => {
        reloadedSaveState = typeof value === "function" ? value(reloadedSaveState) : value;
      },
      setWorkspace: (value: SetStateAction<WorkspaceSnapshot>) => {
        reloadedWorkspace = typeof value === "function" ? value(reloadedWorkspace) : value;
      },
      workspace: reloadedWorkspace,
    } as unknown as Parameters<typeof useActiveResourceSave>[0]);
    await firstSave("first");
    reloadedSavedContent = "remote";
    reloadedWorkspace = workspaceSnapshot("project-2", "remote", "remote-time");

    const afterReloadSave = useActiveResourceSave({
      content: "edited",
      isSuggestionAutoEnabled: false,
      projectId: "project-2",
      requestEnabledPerspectiveSuggestions: () => undefined,
      resource: { type: "chapter", id: "chapter-001", title: "Chapter" },
      savedContent: reloadedSavedContent,
      setSavedContent: (value: SetStateAction<string>) => {
        reloadedSavedContent = typeof value === "function" ? value(reloadedSavedContent) : value;
      },
      setSaveState: (value: SetStateAction<SaveState>) => {
        reloadedSaveState = typeof value === "function" ? value(reloadedSaveState) : value;
      },
      setWorkspace: (value: SetStateAction<WorkspaceSnapshot>) => {
        reloadedWorkspace = typeof value === "function" ? value(reloadedWorkspace) : value;
      },
      workspace: reloadedWorkspace,
    } as unknown as Parameters<typeof useActiveResourceSave>[0]);
    await afterReloadSave("after-reload");
    assert.deepEqual(saveCalls.at(-1), {
      baseUpdatedAt: "remote-time",
      content: "after-reload",
    });

    const forceSave = useActiveResourceSave({
      content: "remote",
      isSuggestionAutoEnabled: false,
      projectId: "project-3",
      requestEnabledPerspectiveSuggestions: () => undefined,
      resource: { type: "chapter", id: "chapter-001", title: "Chapter" },
      savedContent: "remote",
      setSavedContent: () => undefined,
      setSaveState: () => undefined,
      setWorkspace: () => undefined,
      workspace: workspaceSnapshot("project-3", "remote", "server-time"),
    } as unknown as Parameters<typeof useActiveResourceSave>[0]);
    await forceSave("force", { forceOverwrite: true });
    assert.deepEqual(saveCalls.at(-1), { baseUpdatedAt: null, content: "force" });
  } finally {
    moduleWithLoad._load = originalLoad;
  }
});

function chapterResponse(content: string, updatedAt: string, projectId = "project-1"): ChapterResponse {
  return {
    content,
    id: "chapter-001",
    project: {
      id: projectId,
      title: "Project",
      updated_at: updatedAt,
      word_count: content.length,
    },
    title: "Chapter",
    updated_at: updatedAt,
    word_count: content.length,
    writing_synopsis: "saved synopsis",
    writing_synopsis_updated_at: `${updatedAt}-synopsis`,
  };
}

function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, reject, resolve };
}

function workspaceSnapshot(
  projectId = "project-1",
  content = "initial",
  updatedAt = "initial-time",
): WorkspaceSnapshot {
  return {
    active_chapter: {
      content,
      id: "chapter-001",
      title: "Chapter",
      updated_at: updatedAt,
      word_count: content.length,
      writing_synopsis: "saved synopsis",
      writing_synopsis_updated_at: `${updatedAt}-synopsis`,
    },
    chapter_tree: [],
    chapters: [
      {
        id: "chapter-001",
        title: "Chapter",
        updated_at: updatedAt,
        word_count: content.length,
      },
    ],
    document_tree: [],
    perspectives: [],
    project: {
      id: projectId,
      title: "Project",
      updated_at: updatedAt,
      word_count: content.length,
    },
  } as unknown as WorkspaceSnapshot;
}
