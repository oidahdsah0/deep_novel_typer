import { apiFetch } from "./client";
import type {
  PromptProfile,
  PromptProfileUpdate,
  PromptProfileVersion,
  PromptProfileVersionDetail,
  PromptRequestType,
  RestorePromptProfileVersionResponse
} from "./types/index";

export async function updatePromptProfile(
  projectId: string,
  requestType: PromptRequestType,
  input: PromptProfileUpdate,
): Promise<PromptProfile> {
  return await apiFetch<PromptProfile>(
    `/api/projects/${encodeURIComponent(projectId)}/prompt-profiles/${encodeURIComponent(requestType)}`,
    {
      method: "PUT",
      body: JSON.stringify(input),
    },
  );
}

export async function listPromptProfileVersions(
  projectId: string,
  requestType: PromptRequestType,
): Promise<PromptProfileVersion[]> {
  return await apiFetch<PromptProfileVersion[]>(
    `/api/projects/${encodeURIComponent(projectId)}/prompt-profiles/${encodeURIComponent(requestType)}/versions`,
  );
}

export async function getPromptProfileVersion(
  projectId: string,
  requestType: PromptRequestType,
  versionId: string,
): Promise<PromptProfileVersionDetail> {
  return await apiFetch<PromptProfileVersionDetail>(
    `/api/projects/${encodeURIComponent(projectId)}/prompt-profiles/${encodeURIComponent(requestType)}/versions/${encodeURIComponent(versionId)}`,
  );
}

export async function restorePromptProfileVersion(
  projectId: string,
  requestType: PromptRequestType,
  versionId: string,
): Promise<RestorePromptProfileVersionResponse> {
  return await apiFetch<RestorePromptProfileVersionResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/prompt-profiles/${encodeURIComponent(requestType)}/versions/${encodeURIComponent(versionId)}/restore`,
    {
      method: "POST",
    },
  );
}
