import type { ApiConfig } from "./api-configs";
import type { ChapterNode, ChapterSummary } from "./chapters";
import type { DocumentNode, WorkspaceDocument } from "./documents";
import type { GenerationPresetLibrary } from "./generation";
import type { Perspective, SuggestionCard } from "./perspectives";
import type { ProjectSummary } from "./projects";
import type { PromptProfileLibrary } from "./prompts";
import type { TypewriterLayoutSettings } from "./typewriter-layout";

export type WorkspaceSnapshot = {
  project: ProjectSummary;
  active_chapter: {
    id: string;
    title: string;
    content: string;
    word_count: number;
    writing_synopsis: string;
    writing_synopsis_updated_at: string;
    updated_at: string;
  };
  chapters: ChapterSummary[];
  chapter_tree: ChapterNode[];
  documents: WorkspaceDocument[];
  document_tree: DocumentNode[];
  perspectives: Perspective[];
  suggestions: SuggestionCard[];
  api_configs: ApiConfig[];
  generation_presets: GenerationPresetLibrary;
  prompt_profiles: PromptProfileLibrary;
  typewriter_layout_settings: TypewriterLayoutSettings;
};
