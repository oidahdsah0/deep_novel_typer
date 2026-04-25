import type { GenerationPresetKind, PromptRequestType, WorkspaceSnapshot } from "@/lib/api/index";
import type { DocumentGenerationAction, PendingDraftGenerationAction, PresetSaveState } from "./types";

export const severityLabels = {
  calm: "提示",
  focus: "建议",
  risk: "注意",
} as const;

export const sourceLabels = {
  llm: "LLM",
  local: "本地",
} as const;

export const draftActionLabels: Record<PendingDraftGenerationAction, string> = {
  quick_next_paragraph: "快速生成下一段",
  next_paragraph: "生成下一段落",
  next_section: "生成下一部分",
};

export const documentActionLabels: Record<DocumentGenerationAction, string> = {
  polish_selection: "润色选定部分",
  continue_document: "生成后续内容",
};

export const promptRequestTypes: PromptRequestType[] = [
  "perspective_suggestion",
  "polish_selection",
  "quick_generate_next_paragraph",
  "generate_next_paragraph",
  "generate_next_section",
  "generate_chapter_blueprint",
  "polish_document_selection",
  "generate_document_continuation",
  "chat_about_work",
];

export const promptRequestLabels: Record<PromptRequestType, string> = {
  perspective_suggestion: "视角建议",
  polish_selection: "润色选中",
  quick_generate_next_paragraph: "快速生成下一段",
  generate_next_paragraph: "生成下一段落",
  generate_next_section: "生成下一部分",
  generate_chapter_blueprint: "章节基础铺设",
  polish_document_selection: "资料润色选区",
  generate_document_continuation: "资料生成后续",
  chat_about_work: "作品聊天",
};

export const promptPlaceholderOptions: Record<PromptRequestType, string[]> = {
  perspective_suggestion: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.agents}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project}",
    "{input.chapter_title}",
    "{input.current_chapter}",
    "{input.current_paragraph}",
    "{input.perspectives}",
    "{input.textures}",
  ],
  polish_selection: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project_title}",
    "{input.project}",
    "{input.chapter_title}",
    "{input.current_chapter}",
    "{input.selected_text}",
    "{input.polish_prompt}",
    "{input.textures}",
  ],
  generate_next_paragraph: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.agents}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project_title}",
    "{input.project}",
    "{input.chapter_title}",
    "{input.cursor_index}",
    "{input.previous_paragraph}",
    "{input.next_paragraph}",
    "{input.current_chapter}",
    "{input.writing_prompt}",
    "{input.author_persona}",
    "{input.textures}",
  ],
  quick_generate_next_paragraph: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.agents}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project_title}",
    "{input.project}",
    "{input.chapter_title}",
    "{input.cursor_index}",
    "{input.previous_paragraph}",
    "{input.next_paragraph}",
    "{input.current_chapter}",
    "{input.author_persona}",
    "{input.textures}",
  ],
  generate_next_section: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.agents}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project_title}",
    "{input.project}",
    "{input.chapter_title}",
    "{input.cursor_index}",
    "{input.previous_paragraph}",
    "{input.next_paragraph}",
    "{input.current_chapter}",
    "{input.writing_prompt}",
    "{input.author_persona}",
    "{input.textures}",
  ],
  generate_chapter_blueprint: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.agents}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project_title}",
    "{input.project}",
    "{input.chapter_title}",
    "{input.current_chapter}",
    "{input.blueprint_prompt}",
    "{input.author_persona}",
    "{input.textures}",
  ],
  polish_document_selection: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.agents}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project_title}",
    "{input.project}",
    "{input.document_title}",
    "{input.current_document}",
    "{input.selected_text}",
    "{input.polish_prompt}",
    "{input.editor_persona}",
    "{input.textures}",
  ],
  generate_document_continuation: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.agents}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project_title}",
    "{input.project}",
    "{input.document_title}",
    "{input.current_document}",
    "{input.generation_prompt}",
    "{input.editor_persona}",
    "{input.textures}",
  ],
  chat_about_work: [
    "{input.context_pack}",
    "{input.materials}",
    "{input.chapters}",
    "{input.documents}",
    "{input.project_title}",
    "{input.project}",
    "{input.chapter_title}",
    "{input.current_chapter}",
    "{input.chat_messages}",
    "{input.textures}",
  ],
};

export const materialConfigHelpText =
  "控制章节和资料写入请求上下文时的截断上限，例如 max_item_chars 和 max_material_chars；请求模型请使用上方模型配置，不要写进这里。";

export const recentChapterConfigKeys = {
  count: "recent_chapter_count",
  enabled: "recent_chapter_enabled",
} as const;
export const promptProfileConfigKeys = {
  apiConfigId: "api_config_id",
  includeChapterSynopsis: "include_chapter_synopsis",
  temperature: "temperature",
} as const;
export const defaultRecentChapterCount = 2;
export const maxRecentChapterCount = 20;

export const presetSaveLabels: Record<PresetSaveState, string> = {
  idle: "",
  saving: "正在保存设置",
  saved: "已保存",
  error: "保存失败",
};

export const presetListKeys: Record<GenerationPresetKind, keyof WorkspaceSnapshot["generation_presets"]> = {
  writing_mode: "writing_modes",
  quick_generation_mode: "quick_generation_modes",
  chapter_blueprint_mode: "chapter_blueprint_modes",
  author_persona: "author_personas",
  polish_mode: "polish_modes",
  document_polish_mode: "document_polish_modes",
  document_generation_mode: "document_generation_modes",
  editor_persona: "editor_personas",
};
