import type { WorkspaceSnapshot } from "@/lib/api/index";
import { resourceUpdatedAt } from "./activeResourceSaveGuards";
import type { ActiveResource } from "./types";

export type SaveQueue<TPending = unknown> = {
  isDraining: boolean;
  lastSavedContent: string | null;
  lastSavedUpdatedAt: string | null;
  latestSequence: number;
  pending: TPending | null;
};

const saveQueues = new Map<string, SaveQueue<unknown>>();

export function getSaveQueue<TPending>(resourceKey: string): SaveQueue<TPending> {
  const existing = saveQueues.get(resourceKey);
  if (existing) return existing as SaveQueue<TPending>;
  const queue: SaveQueue<TPending> = {
    isDraining: false,
    lastSavedContent: null,
    lastSavedUpdatedAt: null,
    latestSequence: 0,
    pending: null,
  };
  saveQueues.set(resourceKey, queue as SaveQueue<unknown>);
  return queue;
}

export function syncIdleQueueBaseline(
  queue: SaveQueue<unknown>,
  context: {
    resource: ActiveResource;
    savedContent: string;
    workspace: WorkspaceSnapshot;
  },
) {
  if (queue.isDraining || queue.pending) return;
  const updatedAt = resourceUpdatedAt(context);
  if (!updatedAt || updatedAt === queue.lastSavedUpdatedAt) return;
  queue.lastSavedContent = context.savedContent;
  queue.lastSavedUpdatedAt = updatedAt;
}
