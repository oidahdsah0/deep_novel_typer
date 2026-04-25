import { apiFetch } from "./client";
import type {
  Perspective,
  PerspectiveInput
} from "./types/index";

export async function createPerspective(projectId: string, input: PerspectiveInput) {
  return await apiFetch<Perspective>(
    `/api/projects/${encodeURIComponent(projectId)}/perspectives`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function updatePerspective(
  projectId: string,
  perspectiveId: string,
  input: Partial<Perspective>,
) {
  const encodedProjectId = encodeURIComponent(projectId);
  const encodedPerspectiveId = encodeURIComponent(perspectiveId);
  return await apiFetch<Perspective>(
    `/api/projects/${encodedProjectId}/perspectives/${encodedPerspectiveId}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}

export async function deletePerspective(projectId: string, perspectiveId: string) {
  const encodedProjectId = encodeURIComponent(projectId);
  const encodedPerspectiveId = encodeURIComponent(perspectiveId);
  await apiFetch<void>(
    `/api/projects/${encodedProjectId}/perspectives/${encodedPerspectiveId}`,
    {
      method: "DELETE",
    },
  );
}
