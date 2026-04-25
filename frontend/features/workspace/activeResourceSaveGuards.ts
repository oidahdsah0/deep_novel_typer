import { ApiFetchError, type WorkspaceSnapshot } from "@/lib/api/index";
import type { ActiveResource, SaveState } from "@/features/workspace/types";

export function saveFailureState(error: unknown): SaveState {
  return error instanceof ApiFetchError && error.status === 409 ? "conflict" : "error";
}

export function resourceUpdatedAt({
  resource,
  workspace,
}: {
  resource: ActiveResource;
  workspace: WorkspaceSnapshot;
}): string | null {
  if (resource.type === "chapter") {
    return workspace.active_chapter.id === resource.id
      ? workspace.active_chapter.updated_at
      : null;
  }
  return documentNodeUpdatedAt(workspace.document_tree, resource.id);
}

function documentNodeUpdatedAt(
  nodes: WorkspaceSnapshot["document_tree"],
  documentId: string,
): string | null {
  for (const node of nodes) {
    if (node.id === documentId) {
      return node.updated_at;
    }
    const childUpdatedAt = documentNodeUpdatedAt(node.children, documentId);
    if (childUpdatedAt) {
      return childUpdatedAt;
    }
  }
  return null;
}
