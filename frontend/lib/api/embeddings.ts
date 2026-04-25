import { apiFetch } from "./client";
import type {
  ClusterRequest,
  ClusterResponse,
  EmbeddingProjectSettings,
  EmbeddingProjectSettingsUpdate,
  EmbeddingTag,
  EmbeddingTagInput,
  EmbeddingTagUpdate,
  HeatmapRequest,
  HeatmapResponse,
} from "./types/index";

function projectEmbeddingPath(projectId: string, suffix: string) {
  return `/api/projects/${encodeURIComponent(projectId)}${suffix}`;
}

export async function getEmbeddingTags(projectId: string): Promise<EmbeddingTag[]> {
  return await apiFetch<EmbeddingTag[]>(projectEmbeddingPath(projectId, "/embedding-tags"));
}

export async function getEmbeddingSettings(projectId: string): Promise<EmbeddingProjectSettings> {
  return await apiFetch<EmbeddingProjectSettings>(projectEmbeddingPath(projectId, "/embedding-settings"));
}

export async function updateEmbeddingSettings(
  projectId: string,
  input: EmbeddingProjectSettingsUpdate,
): Promise<EmbeddingProjectSettings> {
  return await apiFetch<EmbeddingProjectSettings>(projectEmbeddingPath(projectId, "/embedding-settings"), {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function createEmbeddingTag(
  projectId: string,
  input: EmbeddingTagInput,
): Promise<EmbeddingTag> {
  return await apiFetch<EmbeddingTag>(projectEmbeddingPath(projectId, "/embedding-tags"), {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updateEmbeddingTag(
  projectId: string,
  tagId: string,
  input: EmbeddingTagUpdate,
): Promise<EmbeddingTag> {
  return await apiFetch<EmbeddingTag>(
    projectEmbeddingPath(projectId, `/embedding-tags/${encodeURIComponent(tagId)}`),
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}

export async function deleteEmbeddingTag(projectId: string, tagId: string): Promise<void> {
  await apiFetch<void>(
    projectEmbeddingPath(projectId, `/embedding-tags/${encodeURIComponent(tagId)}`),
    { method: "DELETE" },
  );
}

export async function buildEmbeddingHeatmap(
  projectId: string,
  request: HeatmapRequest,
): Promise<HeatmapResponse> {
  return await apiFetch<HeatmapResponse>(
    projectEmbeddingPath(projectId, "/embeddings/heatmap"),
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

export async function buildEmbeddingClusters(
  projectId: string,
  request: ClusterRequest,
): Promise<ClusterResponse> {
  return await apiFetch<ClusterResponse>(
    projectEmbeddingPath(projectId, "/embeddings/clusters"),
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}
