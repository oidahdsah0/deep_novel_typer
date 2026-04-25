import type { ApiConfig, ApiConfigTemplate } from "./api-configs";
import type { ProjectStatus } from "./common";
import type { VersionSettings } from "./versions";

export type ProjectSummary = {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  genre: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  last_opened_at: string | null;
  deleted_at: string | null;
  chapter_count: number;
  word_count: number;
};

export type ProjectExportOptions = {
  include_debug_logs?: boolean;
  include_token_usage?: boolean;
  include_api_config_summary?: boolean;
};

export type ProjectTransferCounts = {
  chapters: number;
  documents: number;
  chapter_nodes: number;
  document_nodes: number;
  perspectives: number;
  generation_presets: number;
  prompt_profiles: number;
  prompt_profile_versions: number;
  resource_versions: number;
  debug_logs: number;
  token_usage_rows: number;
};

export type ProjectImportResponse = {
  project: ProjectSummary;
  source_project_id: string;
  imported_project_id: string;
  warnings: string[];
  counts: ProjectTransferCounts;
};

export type LibrarySnapshot = {
  projects: ProjectSummary[];
  recent_projects: ProjectSummary[];
  stats: {
    active_count: number;
    trash_count: number;
    total_words: number;
  };
  api_configs: ApiConfig[];
  api_config_templates: ApiConfigTemplate[];
  version_settings: VersionSettings;
};

export type ProjectInput = {
  title: string;
  subtitle?: string;
  description?: string;
  genre?: string;
  status?: ProjectStatus;
};
