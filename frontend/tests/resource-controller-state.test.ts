import assert from "node:assert/strict";
import test from "node:test";

import type { DocumentDetail, WorkspaceSnapshot } from "../lib/api/types";
import {
  applyResourceSnapshot,
  chapterResourceSnapshot,
  documentResourceSnapshot,
  renameActiveResource,
  type WorkspaceResourceState,
} from "../features/workspace/resourceControllerState";

test("chapter workspace snapshot opens the active chapter as saved resource", () => {
  const workspace = workspaceSnapshot("chapter-002", "第二章", "新的章节正文");
  const state = applyResourceSnapshot(
    resourceState(),
    chapterResourceSnapshot(workspace),
    workspace,
  );

  assert.deepEqual(state.resource, {
    type: "chapter",
    id: "chapter-002",
    title: "第二章",
  });
  assert.equal(state.content, "新的章节正文");
  assert.equal(state.savedContent, "新的章节正文");
  assert.equal(state.saveState, "saved");
  assert.equal(state.workspace.active_chapter.id, "chapter-002");
});

test("document detail opens a document without replacing the workspace", () => {
  const current = resourceState();
  const state = applyResourceSnapshot(
    current,
    documentResourceSnapshot({
      content: "资料正文",
      id: "doc-1",
      title: "资料卡",
      updated_at: "document-time",
    } as DocumentDetail),
  );

  assert.deepEqual(state.resource, {
    type: "document",
    id: "doc-1",
    title: "资料卡",
  });
  assert.equal(state.content, "资料正文");
  assert.equal(state.savedContent, "资料正文");
  assert.equal(state.workspace, current.workspace);
});

test("renaming updates only the active matching resource", () => {
  assert.deepEqual(
    renameActiveResource(
      { type: "chapter", id: "chapter-001", title: "旧标题" },
      { type: "chapter", id: "chapter-001", title: "新标题" },
    ),
    { type: "chapter", id: "chapter-001", title: "新标题" },
  );
  assert.deepEqual(
    renameActiveResource(
      { type: "chapter", id: "chapter-001", title: "旧标题" },
      { type: "document", id: "chapter-001", title: "资料标题" },
    ),
    { type: "chapter", id: "chapter-001", title: "旧标题" },
  );
});

function resourceState(): WorkspaceResourceState {
  const workspace = workspaceSnapshot("chapter-001", "第一章", "初始正文");
  return {
    content: "初始正文",
    resource: { type: "chapter", id: "chapter-001", title: "第一章" },
    savedContent: "初始正文",
    saveState: "saved",
    workspace,
  };
}

function workspaceSnapshot(
  chapterId: string,
  title: string,
  content: string,
): WorkspaceSnapshot {
  return {
    active_chapter: {
      content,
      id: chapterId,
      title,
      updated_at: "chapter-time",
      word_count: content.length,
      writing_synopsis: "",
      writing_synopsis_updated_at: "chapter-time",
    },
    chapter_tree: [],
    chapters: [
      {
        id: chapterId,
        title,
        updated_at: "chapter-time",
        word_count: content.length,
      },
    ],
    document_tree: [],
    documents: [],
    generation_presets: {
      author_personas: [],
      chapter_blueprint_modes: [],
      document_generation_modes: [],
      document_polish_modes: [],
      editor_personas: [],
      polish_modes: [],
      quick_generation_modes: [],
      writing_modes: [],
    },
    perspectives: [],
    project: {
      id: "project-1",
      title: "Project",
      updated_at: "project-time",
      word_count: content.length,
    },
    prompt_profiles: { profiles: [] },
    suggestions: [],
  } as unknown as WorkspaceSnapshot;
}
