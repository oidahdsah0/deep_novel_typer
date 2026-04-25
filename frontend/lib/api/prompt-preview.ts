import { apiFetch } from "./client";
import type {
  PromptPreviewInput,
  PromptPreviewResponse
} from "./types/index";

export async function previewPrompt(
  projectId: string,
  input: PromptPreviewInput,
): Promise<PromptPreviewResponse> {
  return await apiFetch<PromptPreviewResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/prompt-preview`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}
