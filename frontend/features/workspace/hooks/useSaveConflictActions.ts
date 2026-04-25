"use client";

import { getDocument, getWorkspaceSnapshot } from "@/lib/api/index";
import { documentResourceSnapshot } from "@/features/workspace/resourceControllerState";
import type { WorkspaceResourceControllerApi } from "./useWorkspaceResourceController";

export function useSaveConflictActions({
  content,
  projectId,
  resourceController,
}: {
  content: string;
  projectId: string;
  resourceController: WorkspaceResourceControllerApi;
}) {
  async function reloadConflictResource() {
    resourceController.setSaveState("saving");
    try {
      if (resourceController.resource.type === "chapter") {
        const nextWorkspace = await getWorkspaceSnapshot(
          projectId,
          resourceController.resource.id,
        );
        resourceController.openWorkspaceChapter(nextWorkspace);
        return;
      }
      const [nextWorkspace, document] = await Promise.all([
        getWorkspaceSnapshot(projectId),
        getDocument(projectId, resourceController.resource.id),
      ]);
      resourceController.openResource(documentResourceSnapshot(document), nextWorkspace);
    } catch {
      resourceController.setSaveState("conflict");
    }
  }

  async function overwriteConflictResource() {
    await resourceController.requestSave(content, { forceOverwrite: true });
  }

  return {
    overwriteConflictResource,
    reloadConflictResource,
  };
}
