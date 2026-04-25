import type { ActiveResource, PendingDraftGenerationState } from "./types";

export function pendingDraftForResource(
  resource: ActiveResource,
  pendingDraft: PendingDraftGenerationState | null,
) {
  return resource.type === "chapter" && pendingDraft?.chapterId === resource.id
    ? pendingDraft
    : null;
}

export function isDraftConfirmationActive(pendingDraft: PendingDraftGenerationState | null) {
  return pendingDraft?.status === "generating" || pendingDraft?.status === "ready";
}
