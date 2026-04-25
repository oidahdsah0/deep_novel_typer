import type {
  ChapterNode,
  ChapterSummary,
  DocumentNode,
  LibrarySnapshot,
  WorkspaceDocument,
  WorkspaceSnapshot,
} from "../types/index";
import { fallbackApiConfigTemplates } from "./api-configs";
import { fallbackGenerationPresets } from "./generation-presets";
import { fallbackPromptProfiles } from "./prompt-profiles";
import { fallbackTypewriterLayoutSettings } from "./typewriter-layout";
import { fallbackVersionSettings } from "./version-settings";

export const emptyLibrary: LibrarySnapshot = {
  projects: [],
  recent_projects: [],
  stats: {
    active_count: 0,
    trash_count: 0,
    total_words: 0,
  },
  api_configs: [],
  api_config_templates: fallbackApiConfigTemplates,
  version_settings: fallbackVersionSettings,
};

export function normalizeLibrarySnapshot(snapshot: LibrarySnapshot): LibrarySnapshot {
  return {
    ...snapshot,
    projects: snapshot.projects ?? [],
    recent_projects: snapshot.recent_projects ?? [],
    api_configs: snapshot.api_configs ?? [],
    api_config_templates:
      snapshot.api_config_templates?.length ? snapshot.api_config_templates : fallbackApiConfigTemplates,
    version_settings: snapshot.version_settings ?? fallbackVersionSettings,
  };
}

export function normalizeWorkspaceSnapshot(snapshot: WorkspaceSnapshot): WorkspaceSnapshot {
  return {
    ...snapshot,
    active_chapter: {
      ...snapshot.active_chapter,
      writing_synopsis: snapshot.active_chapter.writing_synopsis ?? "",
      writing_synopsis_updated_at:
        snapshot.active_chapter.writing_synopsis_updated_at ??
        snapshot.active_chapter.updated_at ??
        "",
      updated_at: snapshot.active_chapter.updated_at ?? "",
    },
    perspectives: snapshot.perspectives ?? [],
    suggestions: snapshot.suggestions ?? [],
    api_configs: snapshot.api_configs ?? [],
    chapter_tree: snapshot.chapter_tree?.length
      ? snapshot.chapter_tree
      : chapterTreeFromLegacy(snapshot.chapters ?? []),
    document_tree: snapshot.document_tree?.length
      ? snapshot.document_tree
      : documentTreeFromLegacy(snapshot.documents ?? []),
    generation_presets: {
      writing_modes: snapshot.generation_presets?.writing_modes?.length
        ? snapshot.generation_presets.writing_modes
        : fallbackGenerationPresets.writing_modes,
      quick_generation_modes: snapshot.generation_presets?.quick_generation_modes?.length
        ? snapshot.generation_presets.quick_generation_modes
        : fallbackGenerationPresets.quick_generation_modes,
      chapter_blueprint_modes: snapshot.generation_presets?.chapter_blueprint_modes?.length
        ? snapshot.generation_presets.chapter_blueprint_modes
        : fallbackGenerationPresets.chapter_blueprint_modes,
      author_personas: snapshot.generation_presets?.author_personas?.length
        ? snapshot.generation_presets.author_personas
        : fallbackGenerationPresets.author_personas,
      polish_modes: snapshot.generation_presets?.polish_modes?.length
        ? snapshot.generation_presets.polish_modes
        : fallbackGenerationPresets.polish_modes,
      document_polish_modes: snapshot.generation_presets?.document_polish_modes?.length
        ? snapshot.generation_presets.document_polish_modes
        : fallbackGenerationPresets.document_polish_modes,
      document_generation_modes: snapshot.generation_presets?.document_generation_modes?.length
        ? snapshot.generation_presets.document_generation_modes
        : fallbackGenerationPresets.document_generation_modes,
      editor_personas: snapshot.generation_presets?.editor_personas?.length
        ? snapshot.generation_presets.editor_personas
        : fallbackGenerationPresets.editor_personas,
    },
    prompt_profiles: snapshot.prompt_profiles ?? fallbackPromptProfiles,
    typewriter_layout_settings:
      snapshot.typewriter_layout_settings ?? fallbackTypewriterLayoutSettings,
  };
}

function chapterTreeFromLegacy(chapters: ChapterSummary[]): ChapterNode[] {
  return chapters.map((chapter) => ({
    id: chapter.id,
    parent_id: null,
    type: "chapter",
    title: chapter.title,
    chapter_id: chapter.id,
    word_count: chapter.word_count,
    updated_at: "",
    children: [],
  }));
}

function documentTreeFromLegacy(documents: WorkspaceDocument[]): DocumentNode[] {
  return documents.map((document) => ({
    id: document.kind,
    parent_id: null,
    type: "markdown",
    title: document.title,
    updated_at: document.updated_at,
    children: [],
  }));
}
