from __future__ import annotations


_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  subtitle TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  genre TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'drafting',
  root_path TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_opened_at TEXT,
  deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS chapters (
  id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  title TEXT NOT NULL,
  order_index INTEGER NOT NULL,
  word_count INTEGER NOT NULL DEFAULT 0,
  file_path TEXT NOT NULL,
  writing_synopsis TEXT NOT NULL DEFAULT '',
  writing_synopsis_updated_at TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chapters_project_order
ON chapters(project_id, order_index);

CREATE TABLE IF NOT EXISTS chapter_nodes (
  id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  parent_id TEXT,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  chapter_id TEXT,
  order_index INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id, parent_id) REFERENCES chapter_nodes(project_id, id) ON DELETE CASCADE,
  FOREIGN KEY (project_id, chapter_id) REFERENCES chapters(project_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chapter_nodes_project_parent_order
ON chapter_nodes(project_id, parent_id, order_index);

CREATE UNIQUE INDEX IF NOT EXISTS idx_chapter_nodes_project_chapter
ON chapter_nodes(project_id, chapter_id)
WHERE chapter_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS chapter_search_meta (
  rowid INTEGER PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(project_id, chapter_id),
  FOREIGN KEY (project_id, chapter_id) REFERENCES chapters(project_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chapter_search_meta_project
ON chapter_search_meta(project_id, chapter_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chapter_search_fts
USING fts5(project_id UNINDEXED, chapter_id UNINDEXED, title, content, tokenize = 'trigram');

CREATE TABLE IF NOT EXISTS project_search_meta (
  rowid INTEGER PRIMARY KEY,
  project_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  resource_subtype TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  path_text TEXT NOT NULL DEFAULT '',
  content_hash TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  extra_json TEXT NOT NULL DEFAULT '{}',
  UNIQUE(project_id, resource_type, resource_id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_search_meta_project_type
ON project_search_meta(project_id, resource_type, resource_id);

CREATE VIRTUAL TABLE IF NOT EXISTS project_search_fts
USING fts5(
  project_id UNINDEXED,
  resource_type UNINDEXED,
  resource_id UNINDEXED,
  resource_subtype UNINDEXED,
  title,
  path_text,
  body,
  tokenize = 'trigram'
);

CREATE TABLE IF NOT EXISTS document_nodes (
  id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  parent_id TEXT,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  file_path TEXT,
  order_index INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id, parent_id) REFERENCES document_nodes(project_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_document_nodes_project_parent_order
ON document_nodes(project_id, parent_id, order_index);

CREATE TABLE IF NOT EXISTS api_configs (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'deepseek',
  kind TEXT NOT NULL DEFAULT 'llm',
  protocol TEXT NOT NULL DEFAULT 'openai_compatible',
  api_key TEXT,
  api_key_required INTEGER NOT NULL DEFAULT 1,
  base_url TEXT NOT NULL,
  mode TEXT NOT NULL DEFAULT 'non_stream',
  model TEXT NOT NULL,
  thinking_enabled INTEGER NOT NULL DEFAULT 1,
  reasoning_effort TEXT NOT NULL DEFAULT 'high',
  max_tokens INTEGER NOT NULL DEFAULT 4096,
  context_window_tokens INTEGER NOT NULL DEFAULT 1000000,
  temperature REAL,
  top_p REAL,
  top_k INTEGER,
  dimensions INTEGER,
  is_default INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS perspectives (
  id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  instructions TEXT NOT NULL,
  api_config_id TEXT,
  is_enabled INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (api_config_id) REFERENCES api_configs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS generation_presets (
  project_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  preset_id TEXT NOT NULL,
  name TEXT NOT NULL,
  content TEXT NOT NULL DEFAULT '',
  is_system INTEGER NOT NULL DEFAULT 0,
  is_hidden INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, kind, preset_id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_generation_presets_project_kind
ON generation_presets(project_id, kind, updated_at);

CREATE TABLE IF NOT EXISTS prompt_profiles (
  project_id TEXT NOT NULL,
  request_type TEXT NOT NULL,
  name TEXT NOT NULL,
  system_template TEXT NOT NULL,
  user_template TEXT NOT NULL,
  output_contract TEXT NOT NULL DEFAULT '',
  chapter_ids_json TEXT NOT NULL DEFAULT '[]',
  document_ids_json TEXT NOT NULL DEFAULT '[]',
  config_json TEXT NOT NULL DEFAULT '{}',
  is_system INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, request_type),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_prompt_profiles_project_updated
ON prompt_profiles(project_id, updated_at);

CREATE TABLE IF NOT EXISTS prompt_profile_versions (
  id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  request_type TEXT NOT NULL,
  version_type TEXT NOT NULL,
  label TEXT,
  note TEXT NOT NULL DEFAULT '',
  snapshot_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_prompt_profile_versions_lookup
ON prompt_profile_versions(project_id, request_type, created_at DESC);

CREATE TABLE IF NOT EXISTS version_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  auto_enabled INTEGER NOT NULL DEFAULT 1,
  auto_interval_minutes INTEGER NOT NULL DEFAULT 10,
  auto_min_chars_changed INTEGER NOT NULL DEFAULT 300,
  auto_min_change_ratio REAL NOT NULL DEFAULT 0.15,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS typewriter_layout_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  first_line_indent_chars REAL NOT NULL DEFAULT 0,
  font_size_px INTEGER NOT NULL DEFAULT 20,
  paragraph_gap_lines REAL NOT NULL DEFAULT 0,
  line_height_multiplier REAL NOT NULL DEFAULT 2.9,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS resource_versions (
  id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  resource_title TEXT NOT NULL,
  version_type TEXT NOT NULL,
  label TEXT,
  note TEXT NOT NULL DEFAULT '',
  file_path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  word_count INTEGER NOT NULL DEFAULT 0,
  char_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resource_versions_lookup
ON resource_versions(project_id, resource_type, resource_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_resource_versions_hash
ON resource_versions(project_id, resource_type, resource_id, content_hash);

CREATE TABLE IF NOT EXISTS model_request_logs (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  model_kind TEXT NOT NULL DEFAULT 'llm',
  request_type TEXT NOT NULL,
  api_config_id TEXT,
  provider TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  request_body_json TEXT NOT NULL DEFAULT '{}',
  response_body_json TEXT NOT NULL DEFAULT '{}',
  context_pack_json TEXT NOT NULL DEFAULT '{}',
  error_message TEXT,
  prompt_tokens INTEGER,
  completion_tokens INTEGER,
  total_tokens INTEGER,
  duration_ms INTEGER,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
  FOREIGN KEY (api_config_id) REFERENCES api_configs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_model_request_logs_created
ON model_request_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_model_request_logs_project_created
ON model_request_logs(project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS model_token_usage_daily (
  date TEXT NOT NULL,
  project_id TEXT NOT NULL DEFAULT '',
  model_kind TEXT NOT NULL DEFAULT 'llm',
  request_type TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
  prompt_tokens INTEGER NOT NULL DEFAULT 0,
  completion_tokens INTEGER NOT NULL DEFAULT 0,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  request_count INTEGER NOT NULL DEFAULT 0,
  unknown_usage_count INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (date, project_id, model_kind, request_type, provider, model)
);

CREATE INDEX IF NOT EXISTS idx_model_token_usage_daily_project_date
ON model_token_usage_daily(project_id, date);

CREATE TABLE IF NOT EXISTS chat_sessions (
  id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '新对话',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  reasoning TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  FOREIGN KEY (project_id, session_id) REFERENCES chat_sessions(project_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_lookup
ON chat_messages(project_id, session_id, created_at);

CREATE TABLE IF NOT EXISTS embedding_tags (
  id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  color TEXT NOT NULL DEFAULT '#d94841',
  is_enabled INTEGER NOT NULL DEFAULT 1,
  embedding_config_id TEXT,
  embedding_model_signature TEXT,
  embedding_vector_ref TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (embedding_config_id) REFERENCES api_configs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_embedding_tags_project_enabled
ON embedding_tags(project_id, is_enabled, updated_at);

CREATE TABLE IF NOT EXISTS embedding_project_settings (
  project_id TEXT PRIMARY KEY,
  embedding_config_id TEXT,
  segmentation_mode TEXT NOT NULL DEFAULT 'word',
  segment_size INTEGER NOT NULL DEFAULT 1,
  algorithm TEXT NOT NULL DEFAULT 'cosine',
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (embedding_config_id) REFERENCES api_configs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS embedding_analysis_runs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  tool_type TEXT NOT NULL,
  status TEXT NOT NULL,
  embedding_config_id TEXT,
  model_signature TEXT NOT NULL DEFAULT '',
  segmentation_mode TEXT NOT NULL,
  algorithm TEXT NOT NULL DEFAULT '',
  params_json TEXT NOT NULL DEFAULT '{}',
  source_content_hash TEXT NOT NULL DEFAULT '',
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (embedding_config_id) REFERENCES api_configs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_embedding_analysis_runs_lookup
ON embedding_analysis_runs(project_id, resource_type, resource_id, tool_type, updated_at DESC);

CREATE TABLE IF NOT EXISTS embedding_analysis_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  token_index INTEGER NOT NULL,
  text TEXT NOT NULL,
  normalized_text TEXT NOT NULL,
  start_offset INTEGER NOT NULL,
  end_offset INTEGER NOT NULL,
  vector_ref TEXT NOT NULL DEFAULT '',
  tag_id TEXT,
  raw_score REAL,
  raw_distance REAL,
  closeness REAL,
  cluster_id TEXT,
  x REAL,
  y REAL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY (run_id) REFERENCES embedding_analysis_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_embedding_analysis_items_run
ON embedding_analysis_items(run_id, token_index);

CREATE TABLE IF NOT EXISTS schema_migrations (
  id TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
