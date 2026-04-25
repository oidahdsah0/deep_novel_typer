"use client";

import type { Dispatch, SetStateAction } from "react";
import { useCallback, useRef, useState, useTransition } from "react";
import type { WorkspaceSnapshot } from "@/lib/api/index";
import {
  applyResourceSnapshot,
  chapterResourceSnapshot,
  renameActiveResource,
  type ResourceContentSnapshot,
} from "../resourceControllerState";
import type { ActiveResource, SaveState } from "../types";

type SaveActiveOptions = { forceOverwrite?: boolean; throwOnError?: boolean };
export type ResourceSaveRequester = (
  nextContent?: string,
  options?: SaveActiveOptions,
) => Promise<void>;

export type WorkspaceResourceControllerApi = {
  commitGeneratedContent: (nextContent: string) => void;
  commitSaveSuccess: (savedContent: string) => void;
  content: string;
  handleResourceDeleted: (
    workspace: WorkspaceSnapshot,
    fallback?: ResourceContentSnapshot,
  ) => void;
  handleResourceRenamed: (renamed: ActiveResource) => void;
  openResource: (
    snapshot: ResourceContentSnapshot,
    workspace?: WorkspaceSnapshot,
  ) => void;
  openWorkspaceChapter: (workspace: WorkspaceSnapshot) => void;
  requestSave: (nextContent?: string, options?: SaveActiveOptions) => Promise<void>;
  resource: ActiveResource;
  saveState: SaveState;
  savedContent: string;
  setContent: Dispatch<SetStateAction<string>>;
  setSaveState: Dispatch<SetStateAction<SaveState>>;
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
  workspace: WorkspaceSnapshot;
};

export type WorkspaceResourceControllerCoreApi = Omit<
  WorkspaceResourceControllerApi,
  "commitGeneratedContent" | "requestSave"
> & {
  commitGeneratedContent: (
    nextContent: string,
    requestSave: ResourceSaveRequester,
  ) => void;
};

export function useWorkspaceResourceController({
  initialWorkspace,
}: {
  initialWorkspace: WorkspaceSnapshot;
}): WorkspaceResourceControllerCoreApi {
  const initialResource = chapterResourceSnapshot(initialWorkspace);
  const [workspace, setWorkspaceState] = useState(initialWorkspace);
  const [resource, setResource] = useState<ActiveResource>(initialResource.resource);
  const [content, setContent] = useState(initialResource.content);
  const [savedContent, setSavedContent] = useState(initialResource.content);
  const [saveState, setSaveState] = useState<SaveState>("saved");
  const [, startTransition] = useTransition();
  const latestWorkspaceRef = useRef(initialWorkspace);
  latestWorkspaceRef.current = workspace;

  const setWorkspace = useCallback<Dispatch<SetStateAction<WorkspaceSnapshot>>>(
    (nextWorkspaceAction) => {
      const nextWorkspace =
        typeof nextWorkspaceAction === "function"
          ? (nextWorkspaceAction as (current: WorkspaceSnapshot) => WorkspaceSnapshot)(
              latestWorkspaceRef.current,
            )
          : nextWorkspaceAction;
      latestWorkspaceRef.current = nextWorkspace;
      setWorkspaceState(nextWorkspace);
    },
    [],
  );

  function openResource(
    snapshot: ResourceContentSnapshot,
    nextWorkspace: WorkspaceSnapshot = latestWorkspaceRef.current,
  ) {
    const next = applyResourceSnapshot(
      {
        content,
        resource,
        savedContent,
        saveState,
        workspace: latestWorkspaceRef.current,
      },
      snapshot,
      nextWorkspace,
    );
    setWorkspace(next.workspace);
    setResource(next.resource);
    setContent(next.content);
    setSavedContent(next.savedContent);
    setSaveState(next.saveState);
  }

  function openWorkspaceChapter(nextWorkspace: WorkspaceSnapshot) {
    openResource(chapterResourceSnapshot(nextWorkspace), nextWorkspace);
  }

  function commitGeneratedContent(
    nextContent: string,
    requestSave: ResourceSaveRequester,
  ) {
    setContent(nextContent);
    startTransition(() => {
      void requestSave(nextContent);
    });
  }

  function commitSaveSuccess(nextSavedContent: string) {
    setSavedContent(nextSavedContent);
    setSaveState("saved");
  }

  function handleResourceDeleted(
    nextWorkspace: WorkspaceSnapshot,
    fallback?: ResourceContentSnapshot,
  ) {
    if (fallback) {
      openResource(fallback, nextWorkspace);
      return;
    }
    setWorkspace(nextWorkspace);
  }

  function handleResourceRenamed(renamed: ActiveResource) {
    setResource((current) => renameActiveResource(current, renamed));
  }

  return {
    commitGeneratedContent,
    commitSaveSuccess,
    content,
    handleResourceDeleted,
    handleResourceRenamed,
    openResource,
    openWorkspaceChapter,
    resource,
    saveState,
    savedContent,
    setContent,
    setSaveState,
    setWorkspace,
    workspace,
  } satisfies WorkspaceResourceControllerCoreApi;
}
