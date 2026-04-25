import assert from "node:assert/strict";
import test from "node:test";

import {
  isDraftConfirmationActive,
  pendingDraftForResource,
} from "../features/workspace/workspaceGenerationControllerState";
import type { ActiveResource, PendingDraftGenerationState } from "../features/workspace/types";

test("pending draft belongs only to the active chapter resource", () => {
  const draft = pendingDraft("chapter-1", "ready");

  assert.equal(pendingDraftForResource(chapterResource("chapter-1"), draft), draft);
  assert.equal(pendingDraftForResource(chapterResource("chapter-2"), draft), null);
  assert.equal(
    pendingDraftForResource({ type: "document", id: "chapter-1", title: "资料" }, draft),
    null,
  );
});

test("draft confirmation is active only while generating or ready", () => {
  assert.equal(isDraftConfirmationActive(pendingDraft("chapter-1", "generating")), true);
  assert.equal(isDraftConfirmationActive(pendingDraft("chapter-1", "ready")), true);
  assert.equal(isDraftConfirmationActive(pendingDraft("chapter-1", "error")), false);
  assert.equal(isDraftConfirmationActive(null), false);
});

function chapterResource(id: string): ActiveResource {
  return { type: "chapter", id, title: id };
}

function pendingDraft(
  chapterId: string,
  status: PendingDraftGenerationState["status"],
): PendingDraftGenerationState {
  if (status === "generating") {
    return { action: "next_paragraph", chapterId, cursorIndex: 0, status };
  }
  if (status === "error") {
    return { action: "next_paragraph", chapterId, error: "failed", status };
  }
  return {
    action: "next_paragraph",
    baseContent: "旧正文",
    chapterId,
    end: 2,
    model: null,
    nextContent: "新正文",
    source: "llm",
    start: 0,
    status,
    text: "新",
  };
}
