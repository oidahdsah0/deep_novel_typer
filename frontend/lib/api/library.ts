import { apiFetch } from "./client";
import { emptyLibrary, normalizeLibrarySnapshot } from "./fallbacks/index";
import type { LibrarySnapshot, ProjectInput, ProjectSummary } from "./types/index";

export async function getLibrarySnapshot(): Promise<LibrarySnapshot> {
  try {
    return normalizeLibrarySnapshot(await apiFetch<LibrarySnapshot>("/api/library"));
  } catch {
    return emptyLibrary;
  }
}

export async function createProject(input: ProjectInput) {
  return await apiFetch<ProjectSummary>("/api/projects", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updateProject(projectId: string, input: Partial<ProjectInput>) {
  return await apiFetch<ProjectSummary>(`/api/projects/${encodeURIComponent(projectId)}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function openProject(projectId: string) {
  return await apiFetch<ProjectSummary>(`/api/projects/${encodeURIComponent(projectId)}/open`, {
    method: "POST",
  });
}

export async function deleteProject(projectId: string) {
  return await apiFetch<ProjectSummary>(`/api/projects/${encodeURIComponent(projectId)}`, {
    method: "DELETE",
  });
}
