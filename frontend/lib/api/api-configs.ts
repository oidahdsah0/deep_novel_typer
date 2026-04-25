import { apiFetch } from "./client";
import type {
  ApiConfig,
  ApiConfigHealthCheckResult,
  ApiConfigInput,
  ApiConfigTemplate
} from "./types/index";

export async function getApiConfigs(): Promise<ApiConfig[]> {
  return await apiFetch<ApiConfig[]>("/api/api-configs");
}

export async function getApiConfigTemplates(): Promise<ApiConfigTemplate[]> {
  return await apiFetch<ApiConfigTemplate[]>("/api/api-configs/templates");
}

export async function createApiConfig(input: ApiConfigInput): Promise<ApiConfig> {
  return await apiFetch<ApiConfig>("/api/api-configs", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updateApiConfig(
  configId: string,
  input: ApiConfigInput,
): Promise<ApiConfig> {
  return await apiFetch<ApiConfig>(
    `/api/api-configs/${encodeURIComponent(configId)}`,
    {
      method: "PUT",
      body: JSON.stringify(input),
    },
  );
}

export async function deleteApiConfig(configId: string): Promise<void> {
  await apiFetch<void>(`/api/api-configs/${encodeURIComponent(configId)}`, {
    method: "DELETE",
  });
}

export async function setDefaultApiConfig(configId: string): Promise<ApiConfig> {
  return await apiFetch<ApiConfig>(
    `/api/api-configs/${encodeURIComponent(configId)}/default`,
    {
      method: "PUT",
    },
  );
}

export async function checkApiConfigHealth(
  configId: string,
): Promise<ApiConfigHealthCheckResult> {
  return await apiFetch<ApiConfigHealthCheckResult>(
    `/api/api-configs/${encodeURIComponent(configId)}/health-check`,
    {
      method: "POST",
    },
  );
}
