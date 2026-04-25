# 架构文档

## 产品形态

Deep Novel Typer 是项目制小说写作工具。启动入口是小说库，用户先管理小说项目，再进入某一本书的写作台。

核心体验分为两层：

- 小说库：创建、搜索、筛选、打开、编辑基本信息、软删除小说项目。
- 写作台：章节正文、资料文档、AI 视角建议三栏工作区。

前端只负责展示和交互编排，不直接操作项目目录，不计算权威字数，不生成权威建议。所有项目结构、排序、字数、删除状态和文件路径都以后端返回为准。

## 存储架构

采用 SQLite + 文件系统的轻量混合架构：

- SQLite 保存小说库元数据、章节/资料树索引、排序、状态、删除标记和最近打开时间。
- SQLite 保存项目级 AI 视角、视角选择的 API 配置引用、续写预设覆盖、请求配置和全局 API 配置池。
- SQLite 保存历史版本元数据、模型 Debug 请求日志和按日 Token usage 聚合。
- SQLite 保存项目级作品聊天会话和消息正文；聊天记录随小说项目隔离。
- SQLite 保存全局打字机版式偏好；该偏好只影响编辑器视觉，不属于任何小说项目。
- 文件系统保存长文本内容，包括章节正文、资料文档和可迁移项目资产。

这样可以同时满足两个目标：

- 小说项目仍然是独立文件夹，便于备份、迁移和人工检查。
- 小说库列表、筛选、删除恢复、更新时间等管理能力由数据库稳定支撑。

## 仓库结构

```text
deep_novel_typer/
  frontend/                 # Next 16 App Router 展示层
    app/                    # 路由入口，只做页面装配、薄 wrapper 或 feature re-export
    styles/                 # 全局 tokens、base、dialog 和响应式样式入口
    features/
      library/              # 小说库页面状态、hooks 和纯组件
      workspace/            # 写作台主容器、共享类型/工具和纯组件
      debug/                # Debug 页面样式和后续可扩展 feature 资源
    lib/api/                # 前端 API client、类型、fallback 与领域请求函数
  backend/
    app/
      Schemas/              # Pydantic 请求、响应和领域数据模型
      Utils/                # 配置、SQLite、CORS、文件存储、锁、路径、LLM client
      Services/             # 小说库、项目、章节、文档、视角、建议、工作台和领域服务包
      APIs/                 # FastAPI 应用、路由、依赖注入、错误映射
    data/
      novel.db              # SQLite 元数据数据库，运行时自动创建
      projects/             # 活跃小说项目目录
      trash/                # 软删除项目目录
    tests/
      fakes.py              # 测试用 fake LLM / fake health checker
      service_factories.py  # 服务测试构造器
      test_*_service.py     # 按领域拆分的后端服务测试
  docs/
  scripts/
```

## 模块化总览

当前架构采用“路由薄、业务厚、边界清”的模块化设计。

前端依赖方向：

```text
frontend/app/*
  -> frontend/features/<domain>/
    -> frontend/lib/api/
    -> frontend/styles/ 或 feature CSS
```

`app/` 目录只承接 Next 路由入口和少量页面装配。小说库主页面实现位于 `features/library/`，写作台实现位于 `features/workspace/`，API 请求统一位于 `lib/api/`。组件不直接拼 API URL，不写权威业务规则；hook 负责状态、副作用和请求编排；纯工具函数放在 feature 内的 `utils.ts`、`treeUtils.ts`、`presetUtils.ts`。

后端依赖方向：

```text
APIs/routers
  -> Services/
    -> Services/<domain>/repository.py
    -> Utils/
    -> Schemas/
```

`APIs` 只负责 HTTP 入参出参、依赖注入和错误映射；`Services` 负责业务编排；复杂领域使用服务包继续拆分 repository、runtime、defaults、contracts、materials 等子职责；`Utils` 提供基础设施；`Schemas` 保存 Pydantic 模型。后端不再保留旧的集中模型入口，也不再保留临时兼容 service 入口。

测试按后端服务领域拆分，`tests/fakes.py` 与 `tests/service_factories.py` 提供共享构造器和 fake 依赖。新增服务时应同步新增或扩展对应 `test_<domain>_service.py`，避免恢复单体测试文件。生成服务测试按能力拆为 presets、draft、polish、document 和 blueprint 五个文件，后续新增生成类型应优先扩展对应窄测试文件，而不是恢复 `test_generation_service.py`。

## 数据边界

SQLite 表：

```text
projects
  id, title, subtitle, description, genre, status
  root_path, created_at, updated_at, last_opened_at, deleted_at

chapters
  id, project_id, title, order_index, word_count, file_path
  writing_synopsis, writing_synopsis_updated_at, created_at, updated_at

chapter_nodes
  id, project_id, parent_id, type, title, chapter_id
  order_index, created_at, updated_at

chapter_search_meta / chapter_search_fts
  project_id, chapter_id, title, content, content_hash, updated_at

project_search_meta / project_search_fts
  project_id, resource_type, resource_id, resource_subtype, title, path_text
  body, content_hash, updated_at, extra_json

document_nodes
  id, project_id, parent_id, type, title, file_path
  order_index, created_at, updated_at

api_configs
  id, name, provider, kind, protocol, api_key, base_url
  api_key_required, mode, model, thinking_enabled, reasoning_effort
  max_tokens, context_window_tokens, temperature, top_p, top_k, dimensions
  is_default, created_at, updated_at

perspectives
  id, project_id, name, description, instructions, api_config_id
  is_enabled, created_at, updated_at

generation_presets
  project_id, kind, preset_id, name, content
  is_system, is_hidden, created_at, updated_at

prompt_profiles
  project_id, request_type, name, system_template, user_template
  output_contract, chapter_ids_json, document_ids_json, config_json
  is_system, created_at, updated_at

prompt_profile_versions
  id, project_id, request_type, version_type, label, note
  snapshot_json, created_at

version_settings
  id, auto_enabled, auto_interval_minutes
  auto_min_chars_changed, auto_min_change_ratio, updated_at

typewriter_layout_settings
  id, first_line_indent_chars, font_size_px, paragraph_gap_lines
  line_height_multiplier, updated_at

resource_versions
  id, project_id, resource_type, resource_id, resource_title
  version_type, label, note, file_path, content_hash
  word_count, char_count, created_at

model_request_logs
  id, project_id, model_kind, request_type, api_config_id, provider, model, status
  request_body_json, response_body_json, context_pack_json, error_message
  prompt_tokens, completion_tokens, total_tokens, duration_ms, created_at

model_token_usage_daily
  date, project_id, model_kind, request_type, provider, model
  prompt_tokens, completion_tokens, total_tokens
  request_count, unknown_usage_count, updated_at

chat_sessions
  id, project_id, title, created_at, updated_at

chat_messages
  id, project_id, session_id, role, content, reasoning, created_at

embedding_tags
  id, project_id, name, description, color, is_enabled
  embedding_config_id, embedding_model_signature, embedding_vector_ref
  created_at, updated_at

embedding_analysis_runs
  id, project_id, resource_type, resource_id, tool_type, status
  embedding_config_id, model_signature, segmentation_mode, algorithm
  params_json, source_content_hash, error_message, created_at, updated_at

embedding_analysis_items
  id, run_id, token_index, text, normalized_text, start_offset, end_offset
  vector_ref, tag_id, raw_score, raw_distance, closeness
  cluster_id, x, y, metadata_json
```

项目目录：

```text
backend/data/projects/{project_id}/
  chapters/
    chapter-001.md
  docs/
    outline.md
    {document_node_id}.md
  versions/
    chapters/{chapter_id}/{version_id}.md
    documents/{document_node_id}/{version_id}.md
  assets/
```

Embedding 向量缓存使用 Chroma 本地持久化目录：

```text
backend/data/chroma/
```

Chroma 只保存向量缓存和安全 metadata，不作为项目权威业务数据库；项目级标签、分析 run、offset、热图分数和图谱坐标仍由 SQLite 保存。Chroma collection 按模型签名 hash 隔离，模型签名至少包含 API 配置 ID、provider、base URL、model 和 dimensions，避免不同向量空间混用。

章节正文仍保存到项目 `chapters/` 下的 `.md` 文件；每章写作梗概作为章节元数据保存在 `chapters.writing_synopsis`，使用独立的 `writing_synopsis_updated_at` 做乐观锁，不推动正文 `updated_at`，也不触发正文历史版本。章节目录的权威结构是 `chapter_nodes`。目录节点只存在于 SQLite，章节节点通过 `chapter_id` 指向 `chapters`。章节排序和移动目录以后端 `move_node` 结果为准：同级顺序写入 `chapter_nodes.order_index`，同时按章节树前序遍历重建 `chapters.order_index`，让默认章节、最近 N 章、搜索跳转和阅读顺序保持一致。旧 `chapter_search_meta` / `chapter_search_fts` 保留给章节窄范围搜索；新版全项目搜索统一使用 `project_search_meta` / `project_search_fts`。删除章节节点时，服务层递归清理目录节点、章节元数据、写作梗概和搜索索引，并把正文文件移到 `data/trash/{project_id}/chapter-nodes/`。

新资料区的权威树结构是 `document_nodes`。目录节点只存在于 SQLite，Markdown 节点在 SQLite 中保存标题、层级和文件路径，正文保存到项目 `docs/` 下的 `.md` 文件。新项目只自动创建一份 ID 为 `outline` 的“基本蓝图”Markdown 节点；旧 `/documents` 摘要接口从 `document_nodes` 中的 `outline` / `design` / `note` 节点派生，不再依赖单独的 `documents` 表。资料排序和移动目录以后端 `move_node` 结果为准，同级顺序写入 `document_nodes.order_index`，正文文件路径不随目录移动而重命名。删除资料节点时，服务层递归清理树节点，并把 Markdown 文件移到 `data/trash/{project_id}/document-nodes/`。

历史版本由 `resource_versions` 保存元数据，正文快照以完整 Markdown 文件保存到项目 `versions/` 目录。自动保存不会逐次生成版本；`VersionService` 根据 `version_settings` 中的时间间隔、变化字数和变化比例决定是否写入 `auto` 版本。恢复历史版本前会先写入 `pre_restore` 版本，再覆盖当前正文。

全局打字机版式由 `typewriter_layout_settings` 保存，固定单行 `id=1`。它是编辑器显示偏好，不跟随作品、章节或资料，不进入项目导入导出，不修改章节正文，不影响字数、搜索、历史版本、AI 上下文或 DOCX 导出。段首缩进以字符宽度为单位，字号以像素为单位，段落距离以视觉空行为单位，行距以正文编辑器 line-height 倍数为单位；段首缩进、段落距离和行距支持 `0.1` 步进，字号使用整数步进，由前端编辑器渲染层实现。正文编辑器使用 CodeMirror 承载章节正文，动态只读、可编辑和版式状态必须通过可重配置 extension 更新，避免重建 `EditorView` 破坏滚动和测量状态。Tab 快速生成和 pending draft 聚焦链路必须把选区设置与滚动分离：先无滚动更新 selection，再用测量坐标做边界夹逼滚动。

请求配置历史由 `prompt_profile_versions` 保存完整 JSON 快照。版本粒度是 `project_id + request_type`；首次保存会写入 `initial` 快照，每次显式保存写入 `manual` 快照，恢复历史前写入 `pre_restore` 快照。请求历史只覆盖当前项目当前请求类型，不和 YAML 默认配置互相反写。

全项目统一搜索由 `Services/search/` 管理。`project_search_meta` 保存资源类型、资源 ID、标题、路径、更新时间、内容 hash 和跳转 metadata；`project_search_fts` 保存标题、路径和正文/模板/版本正文。搜索覆盖章节、资料、请求配置、请求历史、生成预设和资源版本；查询前会幂等检查缺失、过期和已删除资源，保证导入项目或旧项目在第一次搜索时自动补齐索引。

## 后端模块职责

### Schemas

`backend/app/Schemas/` 按领域保存 Pydantic 请求、响应和领域数据模型。公共 Literal / Enum 类型放在 `common.py`；项目、章节、资料、视角、API 配置、生成、提示词、Dry Run、版本、Debug、建议和工作台模型分别放在对应领域文件中。

导入纪律：

- 路由和服务从明确的 `app.Schemas.<domain>` 路径导入。
- `Schemas/__init__.py` 仅作为包级聚合出口，不作为恢复单体模型文件的借口。
- Schema 不 import Service，不写数据库访问，不读取文件系统。

### Utils

- `config.py`：配置公共导入入口，仅 re-export `Settings`、`LLMSettings`、`GenerationSettings` 和 `get_settings()`。真实实现拆在同级模块：`config_types.py` 保存 dataclass 和常量，`config_helpers.py` 保存 YAML / bool / merge helper，`config_llm.py` 读取默认 LLM YAML 和环境变量覆盖，`config_generation.py` 读取生成预设 YAML fallback，`config_settings.py` 聚合运行时设置。
- `db.py`：SQLite 公共导入入口，仅 re-export `AsyncDatabase`。真实实现拆在同级模块：`db_connection.py` 管理连接、PRAGMA、WAL 和事务，`db_schema.py` 保存初始 schema，`db_migrations.py` 保存幂等迁移。
- `cors.py`：CORS 中间件配置。
- `errors.py`：领域异常。
- `ids.py`：ID 生成。
- `storage.py`：线程池包装的异步文件读写和目录移动。
- `locks.py`：项目/章节/文档级异步锁注册表。
- `llm.py`：LLM 公共导入入口，仅 re-export client、schema 和兼容 helper。真实实现拆在同级模块：`llm_schemas.py` 保存 dataclass / Protocol，`llm_client.py` 封装 OpenAI SDK Chat Completions，`llm_options.py` 负责请求参数合并和 request snapshot，`llm_parsing.py` 负责非流式 JSON 响应、usage 和 stream chunk 解析。结构化请求继续使用非流式 JSON，作品聊天继续允许流式自由文本。
- `paths.py`：项目路径、trash 路径解析和越界保护。
- `text.py`：字数、最后非空段落、尾部截断等无副作用文本工具。生成、Prompt Preview、聊天和视角建议的上下文截断必须复用这里的 `tail_text`，避免各服务维护散点 `tail` helper。
- `tree.py`：树形 row 的通用子树收集工具。章节树和资料树 repository 复用该工具，领域模块只保留各自 schema mapping 和排序规则。

### Services

- `LibraryService`：小说库列表、筛选、最近项目聚合。
- `Services/projects/`：管理项目创建、读取、编辑、打开、软删除、恢复和旧项目导入；旧 `project_service.py` 仅作为兼容 re-export。
  - `service.py`：对外业务 API 和薄编排。
  - `repository.py`：`projects`、初始 `chapters` / `document_nodes` / `perspectives` SQL、row mapping、列表和 touch。
  - `lifecycle.py`：项目创建、默认目录/文件写入、旧 manifest 项目导入；启动时只导入已有旧项目，不自动创建示例小说。
  - `trash.py`：项目软删除到 trash、恢复和冲突校验。
- `Services/chapters/`：管理章节目录树、正文读写、字数统计、FTS 索引和软删除；旧 `chapter_service.py` 仅作为兼容 re-export。
  - `service.py`：章节业务编排和外部 Service API。
  - `repository.py`：`chapters` / `chapter_nodes` SQL、row mapping 和排序更新。
  - `tree.py`：章节树构建、子孙校验、路径和移动排序计算。
  - `content.py`：章节正文文件读写、字数计算和版本触发。
  - `search_index.py`：章节 FTS 索引重建、同步和查询。
  - `deletion.py`：章节递归软删除、trash 移动和 manifest。
- `Services/documents/`：管理资料目录树、Markdown 正文读写和软删除；旧 `document_service.py` 仅作为兼容 re-export。
  - `service.py`：资料业务编排和外部 Service API。
  - `repository.py`：`document_nodes` SQL、row mapping 和排序更新。
  - `tree.py`：资料树构建。
  - `content.py`：Markdown 文件读写、自动保存和版本触发。
  - `deletion.py`：资料递归软删除、trash 移动和 manifest。
- `PerspectiveService`：管理项目级 AI 视角。新建项目不自动生成默认视角，新建视角默认关闭；开启状态只影响批量刷新和自动建议，单个手动刷新可直接请求任意视角。
- `ModelRequestQueueService`：统一接收所有外部模型供应商请求，包括 Chat Completions、Embedding 分析和模型健康检查；用 worker 限制真实并发，并按 `manual`、`batch`、`auto` 优先级调度。
- `SuggestionQueueService`：统一接收视角建议请求，做 pending 去重、自动请求替换和 trigger 到模型优先级的映射；它不再维护第二层模型执行 worker，真实供应商并发和优先级统一由 `ModelRequestQueueService` 控制。
- `Services/api_configs/`：读取、保存、删除和健康检查全局 API 配置；供应商模板、运行时 OpenAI SDK overrides、健康检查和 SQL repository 分模块维护，并隐藏 API Key 明文。配置类型 `kind` 创建后不可修改；默认配置和最后一套配置按 `kind` 隔离保护；删除配置会在同一事务中清理 Prompt Profile 的请求级引用，使对应请求自然回退到默认 LLM。
  - `templates.py`：供应商和 LLM / Embedding 默认模板。
  - `runtime.py`：把有效配置转换为 OpenAI SDK 参数和 `extra_body`。
  - `health.py`：LLM / Embedding 健康检查。
  - `repository.py`：`api_configs` 表 SQL 与 row mapping。
  - `service.py`：业务编排。
- `context_limits.py`：集中命名 prompt/generation/chat/suggestion 使用的上下文截断窗口，例如章节/资料 7000 字符、视角建议 2400 字符；新增模型上下文窗口时优先在这里命名。
- `Services/generation/`：管理项目级生成预设、正文/资料生成、润色和章节基础铺设；旧 `generation_service.py` 仅作为兼容 re-export。
  - `service.py`：对外业务 API 和动作编排。
  - `preset_resolution.py`：`generation_presets` 读取、创建、更新、删除，以及 YAML 默认和 SQLite 覆盖/隐藏合并。
  - `request_inputs.py`：各类生成请求的 runtime input 构造、上下文截断和光标前后段解析。
  - `runtime.py`：按请求类型读取 LLM API 配置、复用正式 PromptProfile、调用结构化 JSON LLM。
  - `draft_actions.py`：正文续写和 Tab 快速生成。
  - `polish_actions.py`：正文选区润色。
  - `document_actions.py`：资料选区润色和资料生成后续。
  - `blueprint_actions.py`：章节基础铺设。
  - `local_fallbacks.py`：LLM 不可用或请求失败时的本地兜底与结构化 payload 转换。
- `Services/prompt_preview/`：管理 Dry Run 预览；旧 `prompt_preview_service.py` 仅作为兼容 re-export。
  - `service.py`：Dry Run 编排入口。
  - `request_inputs.py`：视角建议、正文/资料生成、润色、作品聊天等预览 runtime input。
  - `request_options.py`：请求级 API 配置解析、流式/非流式参数展示和 API 配置摘要。
  - `token_estimate.py`：最终 System/User 的粗略 token 估算。
  - `preview_items.py`：复用正式 PromptProfile 构建最终 messages、Context Pack、素材和警告。
- `VersionService`：管理全局保存机制、章节/资料历史版本、版本预览和恢复。
- `ChapterDocxExportService`：管理选中章节的可阅读 `.docx` 正文导出；它只读取项目标题和章节正文，输出 Word OpenXML 包，不承担项目备份、导入或迁移职责。
- `Services/project_transfer/`：管理项目级 zip 导出、备份和导入；manifest、zip 安全检查、导出读取、导入写入和业务编排分模块维护。
  - `archive.py`：zip 打包 / 读取、Zip Slip 防御、checksum 校验和大小限制。
  - `manifest.py`：导出格式标识和版本兼容检查。
  - `exporter.py`：读取 SQLite 项目数据和项目目录文件，生成归档内容。
  - `importer.py`：导入流程编排，保证导入永远创建新项目，不覆盖现有项目。
  - `import_validation.py`：导入数据结构、必需内容文件和统计计数校验。
  - `import_files.py`：内容文件 UTF-8 校验、落盘和导入正文读取工具。
  - `import_database.py`：新项目 ID 分配、API 配置引用映射、事务写 SQLite、重建章节搜索索引。
  - `import_cleanup.py`：导入失败后的项目目录清理。
  - `service.py`：导出 / 导入锁和编排入口。
- `Services/search/`：管理全项目统一搜索；查询解析、FTS repository、索引文档构建、排序、snippet 和搜索编排分模块维护。
  - `service.py`：薄编排入口，负责确保索引、调用 repository 查询和组装响应。
  - `repository.py`：`project_search_meta` / `project_search_fts` 查询、写入和清理。
  - `indexing.py`：统一搜索文档、hash、upsert 和删除工具。
  - `query.py`：query 规范化、scope 到资源类型映射、短词 fallback 判断和 FTS query 构造。
  - `ranking.py`：limit 归一化、FTS / LIKE 搜索排序和 score SQL 规则。
  - `snippets.py`：纯文本 fallback snippet 和 `<mark>` 高亮。
  - `resources.py`：章节、资料、提示词、生成预设、历史版本等可搜索资源构建，meta 当前性判断、stale 计算和结果 metadata 转换。
  - `labels.py`：提示词、预设和版本资源展示标签。
- `Services/embeddings/`：管理通用 Embedding 基础能力和第一批工具箱后端能力。Embedding 是可复用模型基础设施，不是热图私有实现；后续语义搜索、主题曲线、伏笔召回和版本语义差异都应复用同一 runtime 与缓存层。
  - `service.py`：门面入口，管理项目标签、缓存补齐入口和分析服务委托。
  - `analysis_service.py`：热成像与语言簇分析编排、共享 Embedding 准备流程和 run 持久化。
  - `analysis_rows.py`：热图 / 语言簇 item 的 SQLite row 组装。
  - `repository.py`：`embedding_tags`、`embedding_analysis_runs`、`embedding_analysis_items` SQL 和 row mapping。
  - `model_runtime.py`：用 OpenAI-compatible `embeddings.create` 调用供应商，并强制进入 `ModelRequestQueueService`。
  - `chroma_store.py`：本地 Chroma `PersistentClient`、collection、批量 get / upsert 和 metadata 清洗。
  - `cache.py`：模型签名、collection 名、cache id 和文本规范化。
  - `cache_runtime.py`：缓存命中 / 缺失合并、缺失文本批量请求和写回 Chroma。
  - `segmentation.py`：`word` / `sentence` 切片和原文 offset 回映射。
  - `heatmap.py`：cosine / euclidean / manhattan 距离、closeness 归一化和热图 item 构建。
  - `clustering.py`：固定标签簇心分配、簇统计和点位构建。
  - `projection.py`：基于 numpy SVD 的 PCA 二维投影，输出稳定的归一化坐标。
- `tree_movement.py`：章节树和资料树共享的移动计划纯逻辑，负责父目录校验、防止移动到子孙节点、插入位置校验和同级 `order_index` 重算。
- `Services/typewriter_layout/`：管理全局打字机版式偏好。该服务只读写单行全局设置，不读取项目目录，不修改正文，不触发历史版本。
- `DebugLogService`：记录统一模型请求日志、Token usage 和请求耗时，并维护最近 50 次请求 Log；LLM 保存供应商原始请求/返回和 Context Pack，Embedding 只保存脱敏摘要。读取时通过 `debug_readable.py` 派生可读视图，LLM 展示 System/User、请求参数、模型原文、解析 JSON 和 schema error，Embedding 展示工具类型、批次、缓存、usage 和维度摘要。
- `Services/structured_outputs/`：管理 LLM 输出 schema、业务校验和强制契约文本。每类 LLM 请求都必须在这里注册 schema，校验失败抛出 `LLMResponseFormatError` 并由 Debug Log 记录原始响应和 schema error。
  - `schemas.py`：Pydantic 输出模型，包括文本输出和视角建议卡片。
  - `validators.py`：按 `request_type` 分发校验，处理空文本、非法枚举、未知/重复视角和多余字段。
  - `contracts.py`：生成与 validator 保持同步的不可删除输出契约。
- `Services/prompt_profiles/`：管理项目级请求配置，包括 System/User 提示词模板、请求模型选择、素材选择、最近 N 章动态上下文、结构化请求不可删除的 JSON 输出契约、聊天自由文本输出约定和请求配置版本历史；默认模板、契约、素材展开、渲染、版本快照和 SQL repository 分模块维护。
  - `config.py`：请求配置 `config.api_config_id` 解析和清理 helper，保证请求级 API 配置引用只指向存在的 LLM 配置。
  - `defaults.py`：全部请求类型的默认模板。
  - `contracts.py`：结构化请求强制 JSON 输出契约，以及聊天自由文本输出约定。
  - `materials.py`：固定章节、最近 N 章和资料素材展开。
  - `context_builder.py`：构建 `PromptContextPack`，包含 task、project、focus、materials、agents、constraints 和 budget。
  - `context_formatting.py`：上下文文本格式化、fenced block 包装和粗略 token 估算。
  - `rendering.py`：占位符替换和模板清洗。
  - `versions.py`：请求配置历史快照和恢复。
  - `repository.py`：`prompt_profiles` / `prompt_profile_versions` 表 SQL。
  - `service.py`：业务编排。
- `prompt_builder.py`：视角建议卡片 payload 解析与字段规整（`parse_suggestion_payload`）。
- `structured_llm_service.py`：统一调用 LLM、解析 JSON object、调用 `structured_outputs` 做业务 schema 校验，并在成功或失败时写入 Debug Log。
- `ChatService`：管理项目级作品聊天会话、流式聊天请求、聊天 PromptProfile 渲染和 Debug 记录；所有聊天会话入口必须先校验项目存在，聊天不走 `structured_llm_service.py`，但必须进入 `ModelRequestQueueService`。
- `SuggestionService`：根据单个段落和单个视角生成建议卡片；优先调用 LLM，失败或未配置时降级到本地规则。
- `WorkspaceService`：聚合写作台快照。

### APIs

- `main.py`：创建 FastAPI app、注册 CORS、生命周期、路由。
- `dependencies.py`：数据库、文件存储和服务实例装配。
- `routers/`：HTTP endpoint。
- `error_handlers.py`：领域异常到 HTTP 状态码的映射。

## 前端路由

```text
/
  小说库首页。负责项目列表、创建项目、编辑基本信息和删除确认。

/projects/[projectId]
  写作台。负责章节目录树、全项目搜索、Markdown 资料树、AI 视角、请求管理和正文编辑；左右栏显示状态与宽度作为本机 UI 偏好保存到 localStorage。

/debug
  Debug 控制台。负责查看 Token 统计和最近 50 次模型请求 Log；可通过 query 参数 `project_id` 限制在单个小说项目内。LLM 日志详情提供摘要、System、User、参数、原始请求、原始返回和解析结果 Tabs；Embedding 日志详情提供脱敏摘要、参数、请求和返回 Tabs，并保留复制长文本能力。
```

## 前端模块边界

主页面、写作台和 Debug 页都按 feature 组织。`frontend/app/*` 只保留路由入口、薄 wrapper 或 feature re-export，真实实现放在 `frontend/features/library/`、`frontend/features/workspace/` 与 `frontend/features/debug/`。

跨页面共享的应用内弹窗固定放在 `frontend/components/dialog/`。`frontend/app/providers.tsx` 在根布局挂载 `DialogProvider`，业务 hook 通过 `useConfirm()`、`usePrompt()` 和 `useNotice()` 发起 Promise 化确认、输入和提示；业务代码不得再使用 `window.alert` / `window.confirm` / `window.prompt`。

Debug 前端分为三层：

- `DebugClient`：页面级组合层，只挂载范围切换、Token 统计、请求列表和请求详情。
- `features/debug/hooks/`：`useDebugScope` 负责 `project_id` / `return_project_id` 的稳定范围模型，`useDebugLogs` 负责快照刷新、展开项保持和清空确认后的重新读取。
- `features/debug/components/`：范围切换、Token 卡片、请求 Log 列表、详情 Tabs、可读化 Context/System/User/参数/解析结果、原始 JSON/Text 复制能力分别由窄组件维护。

小说库前端分为三层：

- `LibraryClient`：主页面编排层，挂载项目列表、API 配置、保存机制和右侧详情。
- `features/library/hooks/`：项目动作、API 配置动作和左右栏布局偏好。
- `features/library/components/`：项目卡片、项目详情、新建项目、API 配置卡片、健康检查面板和保存机制面板。项目列表固定放在 `components/projects/ProjectList.tsx`；API 配置列表和配置表单固定放在 `components/api-configs/`，其中表单按供应商入口、模型、密钥和请求参数分段，旧 `components/APIConfigFields.tsx` 只保留兼容 re-export。

写作台前端分为三层：

- `WorkspaceClient`：页面级编排层，只负责组合项目状态、active resource controller、generation controller 和各领域 hook 的返回值；不再直接承接大段三栏 JSX、弹窗 JSX、生成域依赖编织或 textarea/caret 细节。
- `features/workspace/hooks/useWorkspaceResourceController.ts`：写作台资源状态控制层，统一管理 `workspace`、active resource、当前正文、已保存正文和保存状态。章节/资料打开、资源删除后回退、资源重命名、生成结果采纳都通过 controller intent 写入状态；真实保存仍委托 `useActiveResourceSave` 的资源级保存队列。
- `features/workspace/resourceControllerState.ts`：resource controller 的纯状态转换函数，覆盖章节快照、资料详情、资源打开和 active 资源重命名，便于用前端单元测试锁定核心状态变更。
- `features/workspace/hooks/`：业务动作和副作用层，管理左右栏布局、自动保存、全项目搜索、章节/资料树动作、生成预设、请求配置、Dry Run、版本历史、视角动作、Embedding 工具箱、打字机版式工具箱、正文/资料生成流程、当前资源保存、DOCX 导出和编辑器交互状态。关键 hook 应导出命名 `XxxApi` 接口，并用 `satisfies XxxApi` 约束返回值；布局组件优先依赖命名接口，而不是大型 `ReturnType<typeof useX>`。写作台跨组件 API 类型集中在 `workspaceInteractionApiTypes.ts` 与 `workspaceToolApiTypes.ts`，hook 文件只 re-export 自己的 `XxxApi`。`useWorkspaceGenerationController` 负责装配生成预设、正文生成、资料生成和 Dry Run 预览，`WorkspaceClient` 不直接手工传递这些 hook 的共享依赖。正文生成 hook 继续细分在 `hooks/draft-generation/`，分别负责正文/快速生成事件编排、章节基础铺设、润色、pending draft 状态机、请求 payload builder 和生成结果提交。请求配置 hook 继续细分在 `hooks/prompts/`，分别负责 profile draft 构建、保存编排、版本历史读取/恢复和请求管理弹窗尺寸状态。Embedding 工具箱状态固定由 `useEmbeddingToolbox` 组合标签 CRUD、设置、热图请求、语言簇请求和结果过期；打字机版式工具箱状态固定由 `useTypewriterLayoutToolbox` 读写全局版式设置。
- `features/workspace/components/`：纯展示和表单组件，只通过 props 接收状态和回调，不直接调用后端 API。

写作台组件按子领域组织：

- `components/layout/`：写作台三栏外壳、编辑区顶部栏、左侧项目导航和弹窗挂载 host。
- `components/search/`：全项目搜索框、scope chips、分组结果和 snippet 展示。
- `components/tree/`：章节树和资料树共享的递归树 UI，包含节点行、操作按钮、创建/重命名输入、拖拽投放区和移动目标类型；只发出 props 回调，不调用后端 API。
- `components/chapters/`：章节树 adapter、新建/重命名表单和章节领域入口；active 判断、字数展示和章节创建类型留在这里。
- `components/documents/`：资料树 adapter、资料表单、Markdown 编辑 / 浏览 / 对照面板；资料类型、active 判断和 Markdown 创建类型留在这里。
- `components/editor/`：CodeMirror 正文编辑器封装、正文光标续写浮动菜单、选区润色菜单和待确认生成内容控件。正文编辑器负责把全局打字机版式渲染成 CodeMirror 可测量布局，并在缩进、字号、段落距离或行距变化后触发布局重测。编辑器 handle 对外区分“只改 selection”和“测量后滚动”两类动作，生成中的 pending focus 不应隐式触发居中滚动。
- `components/typewriter/`：全局打字机版式工具箱，只管理编辑器视觉偏好，不写项目正文。
- `components/generation/`：正文生成、正文润色、资料生成、预设编辑器。
- `components/prompts/`：请求管理、素材选择、模板编辑、输出契约、Dry Run 预览、请求配置历史；`PromptManagerDialog` 和 `PromptPreviewDialog` 只组合子面板，不直接承接大段表单或预览渲染。
- `components/versions/`：章节/资料历史版本弹窗。
- `components/perspectives/`：右侧 AI 视角建议栏；`InsightRail` 只组合右栏，视角列表、视角新增/编辑表单、API 配置下拉、队列按钮和建议卡片分别由窄组件维护。
- `components/embeddings/`：Embedding 工具箱抽屉、热图控制、语言簇面板、SVG 散点图、标签管理、设置面板和热图刻度展示；组件只收 props 和回调，真实请求与状态在 hook 中完成。第一版资料正文可分析并在抽屉显示结果摘要；章节正文热图通过 CodeMirror mark decorations 渲染 token 高亮，刻度 overlay 只显示悬停分数，关闭工具箱或正文变化不会修改正文内容。语言簇图谱使用后端返回的 PCA 坐标、标签锚点、簇统计和 offset，前端只负责筛选、预览、展开弹窗和定位正文。
- `features/model-queue/`：主页面和写作台共用的模型请求队列菜单，只展示当前 LLM / Embedding 请求的安全元信息。

树结构更新、预设列表更新、字数统计、提示词 draft 转换等无副作用逻辑放在 `treeUtils.ts`、`presetUtils.ts`、`utils.ts` 和更窄的页面私有 helper 中。Hook 不渲染 JSX；编辑器 DOM 测量由 `useWritingMenuPositions` 这类局部交互 hook 收敛，`useWorkspaceEditorInteractions` 负责组合正文/资料选区和菜单状态，业务生成 hook 只读取其暴露的光标/选区函数。

生成错误文案统一放在 `features/workspace/generationErrors.ts`。正文生成、章节铺设、正文润色和资料生成不得各自维护一份 `generationErrorMessage`。展示组件不直接弹出确认或提示；破坏性确认优先上提到对应 hook 或 controller，并通过全局 `DialogProvider` 的应用内弹窗完成。

样式层目前采用“全局 class + 领域文件”的过渡方案：`app/globals.css` 只导入 vendor CSS、`styles/*` 和各 feature CSS；跨页面通用 UI 原语放在 `frontend/styles/`，例如 `base.css` 里的 `icon-button` 与 `icon-tooltip`。业务样式分别由 `features/library/library.css`、`features/workspace/workspace.css` 和 `features/debug/debug.css` 聚合，真实规则按领域放在各自 `styles/` 目录；小说库样式拆为 layout、navigation、cards、api-configs 和 forms，写作台样式拆为 layout、trees、search、editor、documents、actions、perspectives、quick-generation、embeddings 和 embedding controls，Debug 样式拆为 layout、log 和 readable。这保留现有 className，避免 CSS Modules 一次性迁移带来的视觉回归。

`frontend/lib/api/` 是唯一前端 API client 层：

- `client.ts`：基础 fetch、错误处理、API base URL、zip/blob 传输和聊天 SSE 流式响应出口；领域文件不得直接调用浏览器 `fetch`。
- `types/`：前端共享响应类型按领域拆分，`types/index.ts` 聚合导出；根部 `types.ts` 只保留兼容 re-export，不允许重新堆类型。
- `fallbacks/`：后端不可用时的非项目展示 fallback 与 normalize 逻辑按领域拆分；小说库 fallback 必须为空库，工作台不得回退到演示小说，前端 generation preset / prompt profile fallback 只保留结构空值，不承载业务默认 prompt。根部 `fallbacks.ts` 只保留兼容 re-export。
- `library.ts`、`workspace.ts`、`chapters.ts`、`documents.ts`、`perspectives.ts`、`api-configs.ts`、`generation.ts`、`prompt-profiles.ts`、`prompt-preview.ts`、`versions.ts`、`suggestions.ts`、`debug.ts`、`project-transfer.ts`、`embeddings.ts`：按业务域封装请求。
- `index.ts`：统一导出；业务代码应从 `@/lib/api/index` 或明确领域文件导入，不恢复单体 `api.ts`。

## 异步、多线程与一致性

- API endpoint 全部使用 `async def`。
- SQLite 访问通过 `aiosqlite`，启用 WAL 和 foreign keys。
- 文件 I/O 通过 `AsyncFileStore` 进入 `ThreadPoolExecutor`，避免阻塞事件循环。
- 项目、章节、资料树和资料正文保存使用 `AsyncLockRegistry` 中的资源锁，避免并发写覆盖。章节和资料正文保存支持 `base_updated_at` 乐观锁：前端保存时提交已知版本，后端发现版本落后则返回 `409`，前端显示保存冲突而不是标记为成功；`base_updated_at` 是后端返回 `updated_at` 的不透明字符串，前端必须原样回传，不得重新格式化或自行生成；保存成功响应携带后端项目摘要，项目总字数以后端为准。
- 写文件使用临时文件加 `os.replace` 原子替换，减少半写入风险。
- 删除项目采用软删除：数据库写入 `deleted_at`，项目目录移动到 `data/trash/`。
- 删除章节节点或资料节点不直接物理销毁文件，统一移动到项目对应的 trash 子目录，并写入删除 manifest。
- 章节树和资料树移动使用后端共享移动计划：前端只发送 `{parent_id, before_node_id}` 意图，后端在锁内校验并返回完整新树。章节树移动会额外重建 `chapters.order_index`。
- 路径统一由 `PathResolver` 生成，禁止请求路径逃逸数据根目录。
- 项目导出使用 zip 格式，默认覆盖项目基本信息、章节/资料树、Markdown 正文、视角、generation presets、prompt profiles、请求历史和资源版本历史；默认不导出 API Key 明文。
- 项目导入永远创建新项目，不覆盖现有项目；导入前校验 manifest 版本、zip 路径、checksum 和 UTF-8 内容，导入时先写项目目录文件，再在单个 SQLite transaction 中写元数据并重建章节搜索索引，失败后清理本次新建目录。

## CORS

CORS 在 `Utils/cors.py` 中集中配置，默认允许：

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3001`

生产环境必须通过 `NOVEL_TYPER_CORS_ORIGINS` 显式收窄来源。

## 生产运行脚本

生产构建和启动固定通过 `scripts/build.sh` 与 `scripts/start.sh`：

- `scripts/build.sh` 会清理 `.next`、按当前 `NEXT_PUBLIC_API_BASE_URL` 或 `BACKEND_HOST/BACKEND_PORT` 构建前端，并把构建期 API Base URL 写入 `.next/novel-api-base-url.txt`。
- 前端 `npm run build` 会先清理 `.next`，再执行 Next 生产构建，并通过 `verify-next-build.mjs` 校验 App Page 入口、`page_client-reference-manifest.js` 和服务端 chunk 完整性，避免 `/projects/[projectId]` 已登记但缺 route entry / client manifest 的半坏产物进入启动阶段。
- `scripts/build.sh` 会在构建后把服务端 SSR `.js` chunk 备份到 `.next-novel-backup/ssr-chunks/`；`verify-next-build.mjs` 会在校验通过时把 `.next/server/app` 路由文件备份到 `.next-novel-backup/server-app/`。备份目录必须在 `.next` 外，避免 Next 启动时清理自己的工作区并误删备份。
- `scripts/start.sh` 启动前会读取 `.next/novel-api-base-url.txt`，校验当前启动请求的 API Base URL 与构建产物一致；不一致时直接失败，要求重新构建。
- `scripts/start.sh` 继续负责同进程组启动 uvicorn 与 `next start`，并在任一子进程退出时清理另一侧；启动前、启动后和高频后台守护中会从 `.next-novel-backup/ssr-chunks/` 与 `.next-novel-backup/server-app/` 恢复缺失文件，规避 Turbopack 生产启动期间的 `ChunkLoadError`、`MODULE_NOT_FOUND` 和 client reference manifest 缺失。

因此，生产烟测使用备用端口时，build 与 start 必须传入同一组后端端口或显式 `NEXT_PUBLIC_API_BASE_URL`；同时通过 `NOVEL_TYPER_CORS_ORIGINS` 放行对应前端来源。

## LLM 视角建议

所有真实外部模型供应商请求都会进入 `ModelRequestQueueService`。该队列是后端唯一的模型出口调度层，覆盖视角建议、正文续写、Tab 快速生成、正文润色、章节基础铺设、资料润色、资料续写、作品聊天、Embedding 热图 / 语言簇分析、LLM 健康检查和 Embedding 健康检查；Dry Run、工作台快照、保存、搜索和 CRUD 不调用外部模型，因此不进入模型队列。

视角建议由 `SuggestionQueueService`、`SuggestionService` 和 `ModelRequestQueueService` 分层编排：

1. 前端提交 `manual`、`batch` 或 `auto` 触发来源；单个刷新携带 `perspective_id`，批量和自动刷新由前端对每个已开启视角分别发起单视角请求。
2. `/api/projects/{project_id}/suggestions` 只把请求交给 `SuggestionQueueService`，不直接调用模型。
3. 队列以 `project_id + chapter_id + perspective_id + paragraph_hash` 作为去重 key，相同 pending 请求复用同一个任务。
4. `SuggestionQueueService` 只把 trigger 映射为模型优先级：`manual > batch > auto`；同一章节同一视角的新自动请求会取消仍在 pending / 等待模型队列的旧自动请求。
5. `SuggestionQueueService` 直接调度单视角任务调用 `SuggestionService.suggest_for_perspective()`，不维护第二层模型 worker；即使多个视角使用同一 API 配置，也不合并到同一次 LLM 请求。
6. `SuggestionService` 发起真实 Chat Completions 前会进入 `ModelRequestQueueService`，由模型队列统一限制所有供应商请求并发，并按 trigger 映射的模型优先级排序。
7. `SuggestionService` 读取当前章节正文、当前段落、项目基本信息和请求配置中勾选的资料摘要；手动单个刷新可指定任意一个视角，即使该视角当前关闭。
8. 按该视角的 `api_config_id` 读取全局 LLM API 配置；视角未选择时使用 `perspective_suggestion` 请求配置里的 `config.api_config_id`，仍未选择时使用默认 LLM 配置。
9. `PromptProfileService` 通过 `Services/prompt_profiles/` 为当前请求构造用户可编辑模板，并自动追加不可删除的 JSON 输出契约，要求模型最多返回一张卡片。
10. `OpenAIChatClient` 只在模型队列 worker 内使用 OpenAI Python SDK 请求 OpenAI-compatible Chat Completions 服务；视角建议强制 `stream=false` 和 `response_format.type=json_object`。
11. 后端按单个视角校验模型 JSON object，只接受当前请求视角的 `perspective_id`，并限制标题/正文长度。
12. 如果某个视角未配置 LLM、请求失败或模型输出不可解析，只让该视角返回 `source=local` 的本地规则建议，其他视角不受影响。

工作台首屏快照不会触发任何视角建议生成，`suggestions` 默认为空，避免打开项目被外部模型响应时间阻塞。真实 LLM 视角建议默认由用户手动触发：可刷新单个视角，也可批量刷新已开启视角。前端的自动建议模式是显式开关；开启后保存章节只等待正文保存成功，随后在后台为每个已开启视角分别发起单视角请求。自动请求仍进入统一模型队列，低优先级执行，可被更新段落替换，并继续写入 Debug Log 和 Token usage。

配置项：

- `backend/config/llm.yaml`：默认 LLM 配置，后端启动时读取一次进入内存。
- `enabled`：是否启用真实 LLM。默认 `true`，但没有 key 时仍会降级到本地规则。
- `api_key_env`：读取密钥的环境变量名，默认 `DEEPSEEK_API_KEY`。
- `base_url`：OpenAI SDK 的基础地址，默认 `https://api.deepseek.com`。
- `model`：模型名，默认 `deepseek-v4-pro`。
- `request.common`：共享的 OpenAI Chat Completions 参数，默认包含结构化请求需要的 `response_format.type=json_object`。
- `request.non_stream`：只用于结构化非流式请求的参数；后端会强制 `stream=false`。
- `NOVEL_TYPER_LLM_CONFIG`：指定另一个 YAML 配置文件路径。
- `NOVEL_TYPER_LLM_API_KEY`、`NOVEL_TYPER_LLM_BASE_URL`、`NOVEL_TYPER_LLM_MODEL`、`NOVEL_TYPER_LLM_TEMPERATURE`、`NOVEL_TYPER_LLM_MAX_TOKENS`、`NOVEL_TYPER_LLM_TOP_P`、`NOVEL_TYPER_LLM_TOP_K`、`NOVEL_TYPER_LLM_TIMEOUT_SECONDS`：运行时覆盖项。

DeepSeek 和 SiliconFlow 的思考模式扩展字段不会作为普通 OpenAI 参数直接传入，而是由 `Services/api_configs/runtime.py` 统一组装成 SDK 的 `extra_body`。DeepSeek 的三档模式映射为：关闭思考发送 `extra_body.thinking.type=disabled`；普通思考发送 `extra_body.thinking.type=enabled` 和顶层 `reasoning_effort=high`；努力思考发送 `extra_body.thinking.type=enabled` 和顶层 `reasoning_effort=max`。后端不再保留手写 `httpx` 请求路径。

主页面的 API 配置子菜单保存全局固定配置，不改全局 YAML，也不需要重启后端。新建配置时必须先选择 API 类型和供应商模板，创建后 `kind` 锁定，不允许把 LLM 改成 Embedding 或反向修改；内置 DeepSeek、OpenAI、Gemini、Grok、SiliconFlow、Ollama、LM Studio 和 vLLM 的 LLM / Embedding 模板。当前可持久化字段包括 `provider`、`kind`、`protocol`、`api_key`、`base_url`、`api_key_required`、`model`、`thinking_enabled`、`reasoning_effort`、`max_tokens`、`context_window_tokens`、`temperature`、`top_p`、`top_k` 和 `dimensions`；`max_tokens` 是发送给供应商的输出 token 预算，`context_window_tokens` 是本地上下文窗口预算检查上限，不直接发送给供应商。`mode` 在数据库中保留为兼容字段，结构化请求运行时使用 `non_stream`，作品聊天请求按请求类型显式切到流式。每个 `kind` 至少保留一套配置；删除默认配置时只在同类型内转移默认项。被视角引用的配置不能删除；被 Prompt Profile 请求级配置引用的配置删除时会清理引用字段，让请求回退到默认 LLM。

小说工程内的视角只能通过下拉菜单选择 `kind=llm` 的配置，不能编辑配置；同一本小说里的不同视角可以选择不同 LLM 配置。Embedding 配置会进入 SQLite 配置池并拥有独立默认项，供写作台 Embedding 工具箱选择，但不参与视角建议或 Prompt Profile 的 LLM 请求配置。API Key 可以写入 SQLite，但不会在 GET 响应里明文返回，前端只拿到 `api_key_configured`。

API 配置健康检查由主页面触发。LLM 检查复用真实 Chat Completions 参数，并验证非流式 JSON object 能力；Embedding 检查调用 embeddings endpoint 并校验返回向量维度。健康检查也进入 `ModelRequestQueueService`，但不写 `model_request_logs`，也不累计 Token usage，避免污染业务 Debug 数据。

Debug 页面从统一模型请求链路写入 SQLite：`model_request_logs` 保存最近 50 次模型请求记录，`model_kind` 区分 `llm` 和 `embedding`；`model_token_usage_daily` 按本机日期、模型类型、请求类型、provider 和 model 聚合 Token usage。Debug 写入锁按 project 分片，最近 50 条清理按间隔触发，避免每次模型请求写入都争同一把全局锁并执行全表 DELETE。结构化写作请求的原始请求体必须包含实际发送的 `stream=false` 和 `response_format.type=json_object`；作品聊天的原始请求体必须包含实际发送的 `stream=true`，不得伪装成 JSON 请求。流式聊天的 response body 保存聚合后的 `content`、`reasoning` 和原始 `chunks`。LLM Debug 记录保留供应商实际 request body / response body 和独立的 `context_pack_json`；Embedding Debug 记录只保存脱敏摘要，包括 model、dimensions、input_count、input_hashes、cache stats、tool/resource/run、embedding_count、embedding_dimensions、usage 和 duration，不保存完整 input 文本、正文切片、资料片段、标签描述或 `data[].embedding` 向量。读取 Debug API 时后端额外返回 `debug_readable` 派生字段，前端无需重新解析原始 JSON 即可展示 LLM Context Pack、System/User、请求参数、模型原始文本、解析后的 payload 和 schema error，或 Embedding 专用摘要。日志不保存 API Key 或 Authorization header；可读视图还会对疑似密钥字段二次脱敏。供应商未返回 usage 时只增加未知 usage 请求数，不把估算值混入 Token 统计。schema 校验失败的 LLM 请求记录为 `status=error`，但仍保留原始响应，方便定位模型没有遵守哪条输出契约；作品聊天不做 JSON schema 校验。

## LLM 正文、资料与铺设生成

写作台正文光标旁的“生成下一段落”“生成下一部分”和“基础铺设”，右侧栏的 Tab 快速生成设置，以及资料编辑器里的“润色选区”和“生成后续”，都由 `GenerationService` 编排：

1. 前端弹窗和右侧栏读取工作台快照里的 `generation_presets`。正文使用 `writing_mode`、`author_persona`、`polish_mode`；Tab 快速生成使用右侧栏里的 `author_persona`；章节基础铺设使用 `chapter_blueprint_mode` 和 `author_persona`；资料使用 `document_polish_mode`、`document_generation_mode`、`editor_persona`。`quick_generation_mode` 兼容保留，但当前不再作为快速生成任务提示词注入 prompt。
2. 默认预设来自 `backend/config/generation.yaml`；用户在项目内改名、改内容、新增或删除时，只写入 `generation_presets`，不会反写 YAML。
3. 读取时先按项目数据库覆盖或隐藏默认预设，再追加项目自建预设；因此同一本书的设置互相跟随，不影响其他小说项目。
4. 正文生成请求会先冻结当前光标位置，并提交光标前最近的非空段落、光标后第一段正文和 `cursor_index`；后端提示词明确要求生成内容插入在这两段之间，不改写、不重复前后段。Tab 快速生成复用同一插入边界，使用独立的 `quick_generate_next_paragraph` 提示词，默认写短、顺滑、低打扰的一段；右侧栏提供 Tab 设置入口，其中模型、Temperature、用户可编辑 System 提示词、User 提示词、是否包含本章梗概和执笔作者人格直接读写同源配置。System/User 提示词中的 `{input.*}` 占位符原样保存，最终由后端统一 renderer 渲染；快速生成不再把旧“快速生成任务”提示词加入 Context Pack。前端收到结果后直接插入光标位置并保存，不再进入待确认。基础铺设同样冻结正文光标位置，要求模型只返回可插入该位置的写作要点，不返回正文；前端采纳后只为每条要点加上外层 `「」` 并插入光标处。随后请求会保存当前资源、当前章节写作梗概和当前选中预设的待保存内容，再由 `PromptContextBuilder` 把章节或资料上下文、操作提示词、作者/编辑人格 Skill，以及请求配置里的章节/资料素材组装为结构化 `PromptContextPack`，最后由统一 renderer 渲染为 Chat Completions messages。
5. 请求配置里的章节素材同时支持固定章节和最近 N 章：固定章节按项目保存，最近 N 章在请求时根据当前章节顺序动态展开，两者合并后按顺序去重。
6. 所有生成请求按请求类型读取 `config.api_config_id` 对应的 `kind=llm` API 配置，未设置时使用默认 LLM 配置，并通过 `ModelRequestQueueService` 统一进入供应商请求 worker。每类请求还可在 `config.temperature` 保存请求级 Temperature，存在时覆盖最终 API 配置里的 Temperature，空值表示继承 API 配置；Tab 快速生成右栏保存到同一个 `config.api_config_id` 和 `config.temperature`。
7. 真实请求进入模型队列前必须用 `Services/llm_context_budget.py` 估算最终 messages 的输入 token，并检查 `input_tokens + max_tokens <= context_window_tokens`。超出时返回上下文超出错误，要求用户减少素材、最近章节、聊天历史或输出预算，不调用供应商，也不降级成本地生成。
8. 所有生成请求强制非流式 JSON object；响应必须先通过 `Services/structured_outputs/` schema 校验，正文和资料 Markdown 片段只从校验后的 `text` 字段提取，章节基础铺设只从校验后的 `points` 字段提取。
9. 如果所选或默认 LLM 配置不可用、请求失败，后端返回 `source=local` 的短文本兜底；如果模型返回 JSON 但不符合 schema，后端返回结构化错误，前端只展示错误和重试入口，不显示采纳按钮。

`Services/prompt_preview/` 提供 Dry Run 能力：前端在请求管理、正文生成/润色和资料生成/润色弹窗里可以预览最终 System/User、结构化 Context Pack、素材展开结果、API 配置摘要、请求参数和粗略 Token 估算。Dry Run 复用 `PromptProfileService` 的正式拼装逻辑，Token 估算基于最终请求消息输入文本，仅用于请求管理界面掌控上下文长度；它不调用 LLM、不写 Debug 请求日志、不消耗 Token，也不能替代供应商返回的 usage。预览会用当前 API 配置的 `context_window_tokens` 检查 `input_tokens + max_tokens`，超过 90% 时给警告，超过 100% 时提示上下文超出。请求管理页传入的 `profile_override` 只用于本次预览，不写数据库。实现上，runtime input、请求参数、token 估算和 item 组装必须继续分文件维护，避免重新堆回单体预览 Service。

`PromptContextPack` 是所有 LLM 请求的统一上下文中间层，固定包含 `task`、`project`、`focus`、`materials`、`agents`、`constraints` 和 `budget`。外层结构由 XML-like 标签渲染，资料和长正文原文放在 fenced block 中，避免资料 Markdown 标题污染 prompt 层级。`focus` 字段使用明确语义名，例如 `chapter_synopsis`、`chapter_excerpt`、`document_excerpt`、`selected_chapter_text`、`selected_document_text`。`chapter_synopsis` 由请求配置 `config.include_chapter_synopsis` 控制，默认开启；开启时只读取当前请求的 `chapter_id` 对应章节梗概，不能批量注入其它章节梗概。正文生成、Tab 快速生成和章节基础铺设都会使用 `insertion_point`、`previous_paragraph`、`next_paragraph` 表达光标插入边界；快速生成不再额外使用 `quick_generation_prompt`，章节基础铺设额外使用 `insertion_target` 和 `blueprint_mode_prompt` 表达插入光标处和程序只负责添加外层 `「」`，避免模型误以为只能续写章节末尾、插入章节头部或自行加编号。旧占位符 `{input.chapters}`、`{input.textures}` 会继续可用，新增 `{input.documents}` 与 `{input.materials}` 作为更清晰的别名；默认模板优先使用 `{input.context_pack}`。

请求管理页的历史按钮读取 `prompt_profile_versions`。恢复历史版本时，后端先把当前配置写为 `pre_restore`，再用选中的快照覆盖 `prompt_profiles`，随后前端刷新当前草稿和历史列表。

## LLM 作品聊天

作品聊天是当前唯一允许流式 + 非 JSON 的 LLM 请求。它仍然是项目级能力：聊天会话和消息保存在 `chat_sessions` / `chat_messages`，按 `project_id` 隔离；前端只负责 SSE 展示、会话切换和轻量编辑。

后端由 `ChatService` 编排：

1. 读取 `chat_about_work` PromptProfile，使用 `PromptProfileService.build_preview()` 生成最终 System/User、素材和 Context Pack。
2. 把 PromptProfile 生成的非空消息放在对话历史前面，再追加用户/助手历史消息，作为实际发送给供应商的 `messages`。
3. 按 `chat_about_work` 的 `config.api_config_id` 选择 LLM API 配置；未设置时使用默认 LLM 配置。
4. 路由返回 SSE 前先准备最终 messages，并用当前 API 配置的 `context_window_tokens` 检查 `input_tokens + max_tokens`。超出时返回普通 JSON 错误，不打开流式响应。
5. 进入 `ModelRequestQueueService`，使用 OpenAI Chat Completions `stream=true`；该请求会移除 `response_format`，不走 `structured_llm_service.py`，也不做 JSON schema 校验。
6. Debug Log 写入实际流式 request body、聚合后的 `content` / `reasoning`、原始 stream `chunks` 和 Context Pack。若供应商 stream usage 可用，则计入 Token usage；否则只计入 unknown usage。
7. 模型流结束后，路由先把用户消息和助手聚合结果持久化到当前会话，并更新会话 `updated_at`；只有保存成功后才发送 SSE `[DONE]`，避免前端看到完成但历史记录丢失。消息读取按 `created_at, id` 排序，保证同一轮用户/助手顺序稳定。

## 架构演进边界

- 新业务先判断归属领域：已有领域优先扩展现有 feature / service 包，不新增横跨全局的单体文件。
- 后端复杂领域优先采用 `service.py + repository.py + 若干纯职责模块` 的包结构；简单领域可以暂时保留单文件 Service，但超过文件大小纪律后必须拆 repository 或 helper。
- 前端新页面必须先进入 `features/<domain>/`，`app/` 只接路由；新交互优先拆成 hook + component + utils，而不是继续扩大页面 client。
- 新 API 路径必须同时更新 `docs/backend-api.md`；新目录、数据流或模块边界必须同步更新本文件；新施工纪律必须同步更新 `docs/development-discipline.md`。
