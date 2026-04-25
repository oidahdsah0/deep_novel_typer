import assert from "node:assert/strict";
import test from "node:test";

import { normalizeWorkspaceSnapshot } from "../lib/api/fallbacks/project";
import type { WorkspaceSnapshot } from "../lib/api/types";

test("workspace fallback does not inject business generation or prompt presets", () => {
  const normalized = normalizeWorkspaceSnapshot({
    active_chapter: {
      content: "",
      id: "chapter-001",
      title: "Chapter",
      updated_at: "",
      word_count: 0,
      writing_synopsis: "",
      writing_synopsis_updated_at: "",
    },
    api_configs: [],
    chapter_tree: [],
    chapters: [],
    document_tree: [],
    documents: [],
    perspectives: [],
    project: {
      id: "project-1",
      title: "Project",
      updated_at: "",
      word_count: 0,
    },
    suggestions: [],
  } as unknown as WorkspaceSnapshot);

  assert.deepEqual(Object.values(normalized.generation_presets).flat(), []);
  assert.deepEqual(normalized.prompt_profiles.profiles, []);
});
