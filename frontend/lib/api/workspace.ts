import { apiFetch } from "./client";
import { normalizeWorkspaceSnapshot } from "./fallbacks/index";
import type { WorkspaceSnapshot } from "./types/index";

export async function getWorkspaceSnapshot(
  projectId: string,
  chapterId?: string,
): Promise<WorkspaceSnapshot> {
  const query = chapterId ? `?chapter_id=${encodeURIComponent(chapterId)}` : "";
  return normalizeWorkspaceSnapshot(
    await apiFetch<WorkspaceSnapshot>(
      `/api/projects/${encodeURIComponent(projectId)}/workspace${query}`,
    ),
  );
}
