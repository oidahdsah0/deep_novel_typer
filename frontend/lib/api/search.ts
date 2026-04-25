import { apiFetch } from "./client";
import type { ProjectSearchResponse, ProjectSearchScope } from "./types/index";

export async function searchProject(
  projectId: string,
  query: string,
  scope: ProjectSearchScope = "all",
  limit = 50,
): Promise<ProjectSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    scope,
    limit: String(limit),
  });
  return await apiFetch<ProjectSearchResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/search?${params.toString()}`,
  );
}
