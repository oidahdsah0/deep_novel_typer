import { apiFetch } from "./client";
import type {
  SuggestionCard
} from "./types/index";

export type SuggestionRequestTrigger = "manual" | "batch" | "auto";

export async function requestSuggestions(
  projectId: string,
  chapterId: string,
  paragraph: string,
  perspectiveId?: string,
  trigger: SuggestionRequestTrigger = "manual",
): Promise<SuggestionCard[]> {
  return await apiFetch<SuggestionCard[]>(
    `/api/projects/${encodeURIComponent(projectId)}/suggestions`,
    {
      method: "POST",
      body: JSON.stringify({
        chapter_id: chapterId,
        paragraph,
        ...(perspectiveId ? { perspective_id: perspectiveId } : {}),
        trigger,
      }),
    },
  );
}
