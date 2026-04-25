import { apiFetch } from "./client";
import type {
  CreateResourceVersionInput,
  ResourceVersion,
  ResourceVersionDetail,
  RestoreResourceVersionResponse,
  VersionSettings,
  VersionSettingsInput,
  VersionedResourceType
} from "./types/index";

export async function updateVersionSettings(
  input: VersionSettingsInput,
): Promise<VersionSettings> {
  return await apiFetch<VersionSettings>("/api/version-settings", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function listResourceVersions(
  projectId: string,
  resourceType: VersionedResourceType,
  resourceId: string,
): Promise<ResourceVersion[]> {
  const params = new URLSearchParams({
    resource_type: resourceType,
    resource_id: resourceId,
  });
  return await apiFetch<ResourceVersion[]>(
    `/api/projects/${encodeURIComponent(projectId)}/versions?${params.toString()}`,
  );
}

export async function createResourceVersion(
  projectId: string,
  input: CreateResourceVersionInput,
): Promise<ResourceVersion> {
  return await apiFetch<ResourceVersion>(
    `/api/projects/${encodeURIComponent(projectId)}/versions`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function getResourceVersion(
  projectId: string,
  versionId: string,
): Promise<ResourceVersionDetail> {
  return await apiFetch<ResourceVersionDetail>(
    `/api/projects/${encodeURIComponent(projectId)}/versions/${encodeURIComponent(versionId)}`,
  );
}

export async function restoreResourceVersion(
  projectId: string,
  versionId: string,
): Promise<RestoreResourceVersionResponse> {
  return await apiFetch<RestoreResourceVersionResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/versions/${encodeURIComponent(versionId)}/restore`,
    {
      method: "POST",
    },
  );
}
