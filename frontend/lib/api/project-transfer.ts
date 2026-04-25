import { apiFetchBlob, apiSendBinary } from "./client";
import type { ProjectExportOptions, ProjectImportResponse } from "./types/index";

export async function exportProjectArchive(
  projectId: string,
  options: ProjectExportOptions = {},
): Promise<Blob> {
  const query = new URLSearchParams({
    include_debug_logs: String(options.include_debug_logs ?? false),
    include_token_usage: String(options.include_token_usage ?? false),
    include_api_config_summary: String(options.include_api_config_summary ?? true),
  });
  return await apiFetchBlob(
    `/api/projects/${encodeURIComponent(projectId)}/export?${query.toString()}`,
  );
}

export async function importProjectArchive(file: File): Promise<ProjectImportResponse> {
  return await apiSendBinary<ProjectImportResponse>("/api/projects/import", file);
}
