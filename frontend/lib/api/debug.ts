import { apiFetch } from "./client";
import { fallbackDebugSnapshot, fallbackModelQueueSnapshot } from "./fallbacks/index";
import type { DebugSnapshot, ModelQueueSnapshot } from "./types/index";

export async function getDebugSnapshot(projectId?: string | null): Promise<DebugSnapshot> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  try {
    return await apiFetch<DebugSnapshot>(`/api/debug${query}`);
  } catch {
    return fallbackDebugSnapshot;
  }
}

export async function clearDebugTokenUsage(projectId?: string | null): Promise<void> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  await apiFetch<void>(`/api/debug/token-usage${query}`, { method: "DELETE" });
}

export async function clearDebugRequestLogs(projectId?: string | null): Promise<void> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  await apiFetch<void>(`/api/debug/request-logs${query}`, { method: "DELETE" });
}

export async function clearDebugAll(projectId?: string | null): Promise<void> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  await apiFetch<void>(`/api/debug/all${query}`, { method: "DELETE" });
}

export async function getModelQueueSnapshot(): Promise<ModelQueueSnapshot> {
  try {
    return await apiFetch<ModelQueueSnapshot>("/api/debug/model-queue");
  } catch {
    return fallbackModelQueueSnapshot;
  }
}
