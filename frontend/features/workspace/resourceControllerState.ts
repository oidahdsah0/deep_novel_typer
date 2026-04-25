import type { DocumentDetail, WorkspaceSnapshot } from "@/lib/api/index";
import type { ActiveResource, SaveState } from "./types";

export type ResourceContentSnapshot = {
  content: string;
  resource: ActiveResource;
  savedContent?: string;
  saveState?: SaveState;
};

export type WorkspaceResourceState = {
  content: string;
  resource: ActiveResource;
  savedContent: string;
  saveState: SaveState;
  workspace: WorkspaceSnapshot;
};

export function chapterResourceSnapshot(
  workspace: WorkspaceSnapshot,
): ResourceContentSnapshot {
  return {
    content: workspace.active_chapter.content,
    resource: {
      type: "chapter",
      id: workspace.active_chapter.id,
      title: workspace.active_chapter.title,
    },
  };
}

export function documentResourceSnapshot(
  document: DocumentDetail,
): ResourceContentSnapshot {
  return {
    content: document.content,
    resource: {
      type: "document",
      id: document.id,
      title: document.title,
    },
  };
}

export function applyResourceSnapshot(
  state: WorkspaceResourceState,
  snapshot: ResourceContentSnapshot,
  workspace: WorkspaceSnapshot = state.workspace,
): WorkspaceResourceState {
  const savedContent = snapshot.savedContent ?? snapshot.content;
  return {
    content: snapshot.content,
    resource: snapshot.resource,
    savedContent,
    saveState: snapshot.saveState ?? "saved",
    workspace,
  };
}

export function renameActiveResource(
  resource: ActiveResource,
  renamed: ActiveResource,
): ActiveResource {
  if (resource.type !== renamed.type || resource.id !== renamed.id) {
    return resource;
  }
  return renamed;
}
