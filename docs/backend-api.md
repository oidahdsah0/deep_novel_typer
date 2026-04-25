# 后端 API 列表

后端基准地址默认是 `http://127.0.0.1:8000`，所有业务接口都放在 `/api` 下。接口层只负责 HTTP 入参、出参和错误映射，业务逻辑必须进入 `Services`。

旧的薄 re-export 文件只用于保持内部导入稳定；API 合约以本文件和 `backend/app/Schemas/` 的领域模型为准。新增或调整公开 URL、请求字段、响应字段时，必须同步更新本文件。

## Health

### GET `/api/health`

返回服务状态。

```json
{
  "status": "ok"
}
```

## Library

### GET `/api/library`

读取小说库首页所需数据：活跃项目列表、最近打开项目、统计信息、全局 API 配置、供应商模板和全局版本设置。

响应：

```json
{
  "projects": [],
  "recent_projects": [],
  "stats": {
    "active_count": 1,
    "trash_count": 0,
    "total_words": 90
  },
  "api_configs": [],
  "api_config_templates": [],
  "version_settings": {
    "auto_enabled": true,
    "auto_interval_minutes": 10,
    "auto_min_chars_changed": 300,
    "auto_min_change_ratio": 0.15,
    "updated_at": null
  }
}
```

## Version Settings

### GET `/api/version-settings`

读取全局保存机制设置。自动保存仍负责当前稿落盘；历史版本只在达到设置阈值时生成。

### PATCH `/api/version-settings`

更新全局自动历史版本策略。

请求：

```json
{
  "auto_enabled": true,
  "auto_interval_minutes": 10,
  "auto_min_chars_changed": 300,
  "auto_min_change_ratio": 0.15
}
```

## Typewriter Layout Settings

打字机版式是全局编辑器视觉偏好，不属于小说项目。它只影响章节正文编辑器里的打字手感，不修改章节正文，不生成历史版本，不影响字数、搜索、AI 请求、项目导入导出或 DOCX 导出。该接口只保存全局视觉参数；CodeMirror 的布局重测、光标聚焦、滚动余量和 selection 策略属于前端实现细节，不应通过项目级或章节级字段表达。

### GET `/api/typewriter-layout-settings`

读取全局打字机版式设置。未保存过时返回默认值。

响应：

```json
{
  "first_line_indent_chars": 0,
  "font_size_px": 20,
  "paragraph_gap_lines": 0,
  "line_height_multiplier": 2.9,
  "updated_at": null
}
```

字段说明：

- `first_line_indent_chars`：段首缩进的视觉字符数，范围 `0` 到 `8`，支持 `0.1` 步进。
- `font_size_px`：正文编辑器字号，范围 `12` 到 `32`，整数步进，默认 `20`。
- `paragraph_gap_lines`：段落之间的视觉空行数，范围 `0` 到 `5`，支持 `0.1` 步进。这是段落距离，不是行距。
- `line_height_multiplier`：正文编辑器行距倍数，范围 `1.0` 到 `4.0`，支持 `0.1` 步进。默认 `2.9`，保持原打字机手感。

### PATCH `/api/typewriter-layout-settings`

更新全局打字机版式设置。后端固定写入单行全局设置，不接收 `project_id`。

请求：

```json
{
  "first_line_indent_chars": 2.5,
  "font_size_px": 24,
  "paragraph_gap_lines": 1.2,
  "line_height_multiplier": 1.8
}
```

## Projects

### GET `/api/projects`

列出小说项目。默认只返回未删除项目。

查询参数：

- `include_deleted=false`：是否包含软删除项目。
- `status`：按项目状态过滤。
- `q`：按书名、副标题、简介、类型模糊搜索。

### POST `/api/projects`

创建项目，并初始化第一章和一份“基本蓝图”资料文档。系统启动和空库状态不会自动创建默认小说；只有调用该接口才会创建项目。项目不会自动创建默认 AI 视角；需要建议卡片时，用户在写作台手动新增并启用视角。

请求：

```json
{
  "title": "沉默港湾",
  "subtitle": "长篇悬疑 · 第一稿",
  "description": "港口旧案与失踪真相。",
  "genre": "悬疑",
  "status": "drafting"
}
```

### GET `/api/projects/{project_id}`

读取项目基本信息、章节索引和资料索引。

### PATCH `/api/projects/{project_id}`

修改项目基本信息。

请求：

```json
{
  "title": "沉默港湾",
  "subtitle": "第二稿",
  "description": "新的核心设定",
  "genre": "悬疑",
  "status": "revising"
}
```

### POST `/api/projects/{project_id}/open`

标记项目最近打开时间，并返回项目基本信息。

### DELETE `/api/projects/{project_id}`

软删除项目。前端必须在调用前做显式确认。后端会写入 `deleted_at`，并将项目目录移动到 `backend/data/trash/`。

### POST `/api/projects/{project_id}/restore`

恢复软删除项目。后端会清空 `deleted_at`，并将项目目录从 trash 移回 projects。

### GET `/api/projects/{project_id}/workspace`

读取写作台快照：项目信息、指定或默认章节、章节列表、章节树、资料列表、资料树、AI 视角列表、全局 API 配置列表、续写/润色预设、请求配置和右侧建议卡片。为了保证打开项目不被外部模型请求阻塞，快照不会自动生成视角建议，`suggestions` 默认为空；真实 LLM 视角建议只由用户手动刷新，或前端显式开启自动建议模式后在后台触发。

快照还包含 `typewriter_layout_settings`，用于首屏渲染全局打字机版式偏好。该字段与当前项目无关，只是随工作台快照一起返回，避免前端先显示默认版式再二次请求。

`active_chapter` 除正文 `content`、字数和 `updated_at` 外，还包含当前章节绑定的 `writing_synopsis` 与独立乐观锁字段 `writing_synopsis_updated_at`。章节写作梗概随章节元数据保存；章节删除会同步删除，项目软删除时随项目隐藏和恢复。

查询参数：

- `chapter_id`：指定当前章节。不传时取排序第一章。

### GET `/api/projects/{project_id}/export`

导出指定小说项目为 zip 备份包。响应类型为 `application/zip`，用于浏览器下载。
该接口只用于项目迁移 / 备份；可阅读正文的 Word 文档导出走章节域的 `POST /api/projects/{project_id}/chapters/export-docx`。

查询参数：

- `include_debug_logs=false`：是否包含脱敏后的 Debug 请求日志。
- `include_token_usage=false`：是否包含 Token usage 聚合行。
- `include_api_config_summary=true`：是否包含被视角引用的 API 配置摘要。

导出包格式：

```text
project-export.zip
  manifest.json
  checksums.json
  data/project.json
  data/chapters.json
  data/chapter_nodes.json
  data/document_nodes.json
  data/perspectives.json
  data/api_config_refs.json
  data/generation_presets.json
  data/prompt_profiles.json
  data/prompt_profile_versions.json
  data/resource_versions.json
  content/chapters/*.md
  content/docs/*.md
  content/versions/**/*.md
```

`manifest.json` 固定包含 `format="deep-novel-typer.project-export"` 和 `format_version=2`。v2 归档不再包含旧 `data/documents.json`，资料元数据只从 `data/document_nodes.json` 导入导出。导出默认不包含 API Key 明文；API 配置只导出供应商、模型、Endpoint、是否配置过 key 等摘要字段。

### POST `/api/projects/import`

导入项目 zip 备份包。请求体为原始 zip bytes，`Content-Type: application/zip`。导入永远创建新项目，不覆盖现有项目；如果原项目 ID 已存在，会生成新 ID，并在标题后追加“导入副本”。

响应：

```json
{
  "project": {
    "id": "silent-harbor-2",
    "title": "沉默港湾（导入副本）",
    "subtitle": "",
    "description": "",
    "genre": "悬疑",
    "status": "drafting",
    "created_at": "2026-04-26T00:00:00+00:00",
    "updated_at": "2026-04-26T00:00:00+00:00",
    "last_opened_at": null,
    "deleted_at": null,
    "chapter_count": 4,
    "word_count": 12000
  },
  "source_project_id": "silent-harbor",
  "imported_project_id": "silent-harbor-2",
  "warnings": [
    "原 API 配置 default-api 在本机不存在，相关视角已设为默认配置。"
  ],
  "counts": {
    "chapters": 4,
    "documents": 0,
    "chapter_nodes": 5,
    "document_nodes": 8,
    "perspectives": 3,
    "generation_presets": 4,
    "prompt_profiles": 6,
    "prompt_profile_versions": 8,
    "resource_versions": 12,
    "debug_logs": 0,
    "token_usage_rows": 0
  }
}
```

导入会校验 zip 路径、必需 JSON、文件 checksum 和 UTF-8 内容。若数据库写入失败，会回滚事务并清理本次新建项目目录。

## Search

### GET `/api/projects/{project_id}/search`

全项目统一搜索，覆盖章节、资料、请求配置、请求历史、生成预设和资源版本。后端使用 `project_search_meta` / `project_search_fts` 维护统一 SQLite FTS5 索引；三字及以上查询走 trigram FTS，短词查询走索引内容表的 `LIKE` fallback，不依赖前端遍历全文。

查询参数：

- `q`：搜索词。
- `scope=all`：搜索范围，可选 `all`、`chapters`、`documents`、`prompts`、`presets`、`versions`。
- `limit=50`：结果上限，最大 100。

响应：

```json
{
  "query": "蓝色证词",
  "scope": "all",
  "results": [
    {
      "resource_type": "chapter",
      "resource_id": "chapter-002",
      "resource_subtype": "chapter",
      "title": "第二章 回声",
      "path": ["第一卷"],
      "updated_at": "2026-04-26T00:00:00+00:00",
      "score": -0.82,
      "matches": [
        {
          "field": "content",
          "snippet": "林澈在旧码头找到<mark>蓝色证词</mark>。"
        }
      ],
      "metadata": {
        "chapter_id": "chapter-002",
        "node_id": "chapter-002"
      }
    }
  ]
}
```

## Embeddings

Embedding 是通用模型基础能力，当前第一批公开接口服务于写作台 Embedding 工具箱。全局 Embedding API 配置仍在主页面 API 配置中维护；工具箱接口只能引用已有 `kind=embedding` 的配置。真实 Embedding 请求会进入 `ModelRequestQueueService`，不会在队列快照中暴露正文全文、向量、API Key 或 Authorization header。

### GET `/api/projects/{project_id}/embedding-tags`

读取当前项目的语义标签。标签用于语义热成像和语言簇；标签 embedding 会在分析时按“名称 + 描述”生成并缓存。

响应：

```json
[
  {
    "id": "danger",
    "project_id": "silent-harbor",
    "name": "危险",
    "description": "威胁、失控、死亡风险",
    "color": "#d94841",
    "is_enabled": true,
    "embedding_config_id": null,
    "embedding_model_signature": null,
    "embedding_vector_ref": null,
    "created_at": "2026-06-12T00:00:00+00:00",
    "updated_at": "2026-06-12T00:00:00+00:00"
  }
]
```

### POST `/api/projects/{project_id}/embedding-tags`

新增项目级语义标签。

请求：

```json
{
  "name": "危险",
  "description": "威胁、失控、死亡风险",
  "color": "#d94841",
  "is_enabled": true
}
```

### PATCH `/api/projects/{project_id}/embedding-tags/{tag_id}`

更新语义标签。修改 `name` 或 `description` 会清理该标签已保存的 embedding 引用；下次分析会重新生成标签 embedding。

请求：

```json
{
  "description": "威胁、失控、死亡风险、压迫感",
  "is_enabled": true
}
```

### DELETE `/api/projects/{project_id}/embedding-tags/{tag_id}`

删除项目级语义标签。

### GET `/api/projects/{project_id}/embedding-settings`

读取当前项目的 Embedding 工具箱默认设置。该设置仅为工具箱的本机偏好，后端 heatmap/clusters 请求**不会**自动读取它；请求体省略字段时使用接口自身默认值（`segmentation_mode=word`、`segment_size=1`、`algorithm=cosine`）。工具箱前端会用本设置预填表单，用户可在每次请求时覆盖。

响应：

```json
{
  "project_id": "silent-harbor",
  "api_config_id": "siliconflow-qwen-embedding",
  "segmentation_mode": "word",
  "segment_size": 1,
  "algorithm": "cosine",
  "updated_at": "2026-06-12T00:00:00+00:00"
}
```

如果项目尚未保存过设置，后端返回默认值：`api_config_id=null`、`segmentation_mode=word`、`segment_size=1`、`algorithm=cosine`、`updated_at=null`。

### PATCH `/api/projects/{project_id}/embedding-settings`

更新当前项目的 Embedding 工具箱默认设置。`api_config_id` 只能引用已有 `kind=embedding` 的全局 API 配置，不能引用 LLM 配置；传入空字符串会被归一为 `null`，表示使用默认 Embedding 配置。

请求：

```json
{
  "api_config_id": "siliconflow-qwen-embedding",
  "segmentation_mode": "word",
  "segment_size": 1,
  "algorithm": "cosine"
}
```

字段说明：

- `api_config_id`：可选，指定项目默认 Embedding API 配置。为空时使用默认 Embedding 配置。
- `segmentation_mode`：默认 `word`，可选 `word` 或 `sentence`。
- `segment_size`：默认 `1`，范围 `1` 到 `12`。用于把连续 token / 句子合并成分析片段。
- `algorithm`：默认 `cosine`，可选 `cosine`、`euclidean` 或 `manhattan`。

### POST `/api/projects/{project_id}/embeddings/heatmap`

为当前章节或资料生成语义热成像结果。后端会读取资源正文、按指定粒度切片、用 Chroma 补齐 token / 标签 embedding 缓存、计算 token 到每个标签的距离，并保存本次分析 run 和 item 记录。

请求：

```json
{
  "resource_type": "chapter",
  "resource_id": "chapter-001",
  "api_config_id": "siliconflow-qwen-embedding",
  "segmentation_mode": "word",
  "segment_size": 1,
  "algorithm": "cosine",
  "tag_ids": ["danger", "mist"],
  "range": {
    "start_offset": null,
    "end_offset": null
  },
  "force_reembed": false
}
```

字段说明：

- `resource_type`：`chapter` 或 `document`。
- `segmentation_mode`：`word` 或 `sentence`。
- `segment_size`：默认 `1`，范围 `1` 到 `12`。用于把连续 token / 句子合并成分析片段。
- `algorithm`：`cosine`、`euclidean` 或 `manhattan`。
- `tag_ids`：为空时使用当前项目已启用标签；不为空时按指定标签分析，可包含未启用标签。
- `range`：可选，限制分析的原文 offset 范围。响应 item 的 offset 仍按完整正文坐标返回。
- `force_reembed`：是否绕过现有 Chroma 缓存重新请求 embedding。

响应：

```json
{
  "run_id": "embedding-run-abc123",
  "status": "success",
  "resource_type": "chapter",
  "resource_id": "chapter-001",
  "model_signature": "siliconflow|https://api.siliconflow.cn/v1|Qwen/Qwen3-Embedding-8B|4096",
  "model_signature_hash": "hash",
  "segmentation_mode": "word",
  "segment_size": 1,
  "algorithm": "cosine",
  "tags": [],
  "items": [
    {
      "token_index": 0,
      "text": "码头",
      "normalized_text": "码头",
      "start_offset": 12,
      "end_offset": 14,
      "scores": {
        "danger": {
          "raw_score": 0.72,
          "raw_distance": null,
          "closeness": 0.91
        }
      },
      "nearest_tag_id": "danger"
    }
  ],
  "token_cache": {
    "requested_count": 120,
    "unique_count": 86,
    "cache_hit_count": 70,
    "cache_miss_count": 16
  },
  "tag_cache": {
    "requested_count": 2,
    "unique_count": 2,
    "cache_hit_count": 2,
    "cache_miss_count": 0
  },
  "warnings": []
}
```

### POST `/api/projects/{project_id}/embeddings/clusters`

为当前章节或资料生成语言簇结果。第一版使用固定标签簇心模式：标签 embedding 作为不可移动语义锚点，每个 token / 句子分配给距离最近的标签，并把 token 点和标签锚点一起做 PCA 二维投影。后端会保存本次分析 run 和 item 记录。

请求：

```json
{
  "resource_type": "chapter",
  "resource_id": "chapter-001",
  "api_config_id": "siliconflow-qwen-embedding",
  "segmentation_mode": "sentence",
  "segment_size": 1,
  "algorithm": "cosine",
  "cluster_mode": "fixed_tag_centers",
  "tag_ids": ["danger", "clue"],
  "range": null,
  "force_reembed": false
}
```

字段说明：

- `segmentation_mode`：`word` 或 `sentence`。
- `segment_size`：默认 `1`，范围 `1` 到 `12`。用于把连续 token / 句子合并成分析片段。
- `algorithm`：`cosine`、`euclidean` 或 `manhattan`。
- `cluster_mode`：当前只支持 `fixed_tag_centers`。后续可扩展为标签初始化 K-Means。
- `projection`：响应当前固定为 `pca`。
- 标签少于 2 个时仍返回单簇归属和 warning，不启用迭代 K-Means。
- 空文本或空 range 会返回空 `points`、稳定的标签锚点和 warning。

响应：

```json
{
  "run_id": "embedding-run-def456",
  "status": "success",
  "resource_type": "chapter",
  "resource_id": "chapter-001",
  "model_signature": "siliconflow|https://api.siliconflow.cn/v1|Qwen/Qwen3-Embedding-8B|4096",
  "model_signature_hash": "hash",
  "segmentation_mode": "sentence",
  "segment_size": 1,
  "algorithm": "cosine",
  "cluster_mode": "fixed_tag_centers",
  "projection": "pca",
  "tags": [],
  "points": [
    {
      "token_index": 0,
      "text": "码头升起海雾。",
      "normalized_text": "码头升起海雾。",
      "start_offset": 12,
      "end_offset": 19,
      "cluster_id": "clue",
      "tag_id": "clue",
      "raw_score": 0.74,
      "raw_distance": null,
      "closeness": 0.87,
      "x": -0.42,
      "y": 0.18
    }
  ],
  "clusters": [
    {
      "cluster_id": "clue",
      "tag_id": "clue",
      "name": "线索",
      "color": "#3b82f6",
      "point_count": 12,
      "average_closeness": 0.81,
      "x": 0.2,
      "y": -0.1
    }
  ],
  "tag_anchors": [
    {
      "tag_id": "clue",
      "name": "线索",
      "color": "#3b82f6",
      "x": 0.2,
      "y": -0.1
    }
  ],
  "token_cache": {
    "requested_count": 24,
    "unique_count": 24,
    "cache_hit_count": 20,
    "cache_miss_count": 4
  },
  "tag_cache": {
    "requested_count": 2,
    "unique_count": 2,
    "cache_hit_count": 2,
    "cache_miss_count": 0
  },
  "warnings": []
}
```

## Documents

资料区使用 SQLite 保存目录树元数据，Markdown 正文仍保存为项目目录下的 `.md` 文件。新项目只自动创建一份 ID 为 `outline` 的“基本蓝图”Markdown 节点。`document_nodes` 是资料元数据的唯一权威结构，目录树和正文读取都以节点 ID 为准。

### GET `/api/projects/{project_id}/documents`

读取资料摘要索引。该接口为工作区旧字段保留响应形状，仅从 `document_nodes` 中 ID 为 `outline`、`design`、`note` 的 Markdown 节点派生；新功能应优先使用 `/documents/tree` 和 Markdown 节点接口。

### GET `/api/projects/{project_id}/documents/tree`

读取项目资料树。

响应：

```json
[
  {
    "id": "world",
    "parent_id": null,
    "type": "folder",
    "title": "世界观",
    "updated_at": "2026-04-25T00:00:00+00:00",
    "children": [
      {
        "id": "harbor-legends",
        "parent_id": "world",
        "type": "markdown",
        "title": "港口传说",
        "updated_at": "2026-04-25T00:00:00+00:00",
        "children": []
      }
    ]
  }
]
```

### POST `/api/projects/{project_id}/documents/nodes`

新建资料目录或 Markdown 文本。`parent_id` 为空时创建根节点；不为空时父节点必须是目录。

请求：

```json
{
  "type": "markdown",
  "title": "港口传说",
  "parent_id": "world",
  "content": "## 传说\n\n潮水会带回旧案。"
}
```

### PATCH `/api/projects/{project_id}/documents/nodes/{node_id}`

重命名资料目录或 Markdown 文本。

请求：

```json
{
  "title": "港口传说索引"
}
```

### PATCH `/api/projects/{project_id}/documents/nodes/{node_id}/move`

移动资料目录或 Markdown 文本。`parent_id=null` 表示移动到根目录；`before_node_id=null` 表示放到目标目录末尾。目标父节点必须是目录，后端会禁止把目录移动到自己的子孙节点内，并统一重算同级 `order_index`。

请求：

```json
{
  "parent_id": "world",
  "before_node_id": "harbor-legends"
}
```

响应：

```json
{
  "document_tree": []
}
```

### DELETE `/api/projects/{project_id}/documents/nodes/{node_id}`

删除资料目录或 Markdown 文本。目录会递归删除子目录和 Markdown 文本；对应 `.md` 文件会移动到 `backend/data/trash/{project_id}/document-nodes/` 下，并写入 `manifest.json`，不会直接物理销毁。

### GET `/api/projects/{project_id}/documents/{document_id}`

读取 Markdown 文本正文。目录节点没有正文，会返回冲突错误。

### PUT `/api/projects/{project_id}/documents/{document_id}`

保存 Markdown 文本正文，并更新资料节点与项目更新时间。

请求：

```json
{
  "content": "## 传说\n\n新的线索。",
  "base_updated_at": "2026-04-26T00:00:00+00:00"
}
```

`base_updated_at` 可为空；传入时表示客户端基于哪个资料版本保存。该字段是后端返回的 `updated_at` 不透明字符串，客户端必须原样回传最近一次 GET / 保存响应中的值，不得重新格式化或自行生成。若服务端当前 `updated_at` 已变化，返回 `409`，前端不得把该资源标记为已保存。保存成功响应会在资料详情外额外返回 `project` 摘要，前端应以后端 `project.updated_at` / `project.word_count` 为准。保存后，后端会根据 `/api/version-settings` 的策略判断是否为该资料文本写入一个 `auto` 历史版本。

## API Configs

### GET `/api/api-configs`

读取主页面维护的全局 API 配置列表。配置按 `kind` 区分 LLM 和 Embedding；写作台视角和 Prompt Profile 的 LLM 请求配置只能选择 `kind=llm`，Embedding 工具箱只能选择 `kind=embedding`。API Key 不会在响应里明文返回，只返回是否存在有效 key。

响应：

```json
[
  {
    "id": "default-api",
    "name": "默认 API 配置",
    "provider": "deepseek",
    "kind": "llm",
    "protocol": "openai_compatible",
    "base_url": "https://api.deepseek.com",
    "api_key_configured": false,
    "api_key_required": true,
    "mode": "non_stream",
    "model": "deepseek-v4-pro",
    "thinking_enabled": true,
    "reasoning_effort": "high",
    "max_tokens": 4096,
    "context_window_tokens": 1000000,
    "temperature": null,
    "top_p": null,
    "top_k": null,
    "dimensions": null,
    "is_default": true,
    "created_at": "2026-04-25T00:00:00+00:00",
    "updated_at": "2026-04-25T00:00:00+00:00"
  }
]
```

### GET `/api/api-configs/templates`

读取内置 API 供应商模板。主页面新建配置时使用模板填充默认 Endpoint、模型、密钥要求和可用参数。当前模板覆盖 DeepSeek、OpenAI、Gemini、Grok、SiliconFlow、Ollama、LM Studio 和 vLLM，并分别提供 LLM 与 Embedding 类型。

响应片段：

```json
[
  {
    "provider": "openai",
    "provider_label": "OpenAI",
    "kind": "embedding",
    "protocol": "openai_compatible",
    "name": "OpenAI Embedding",
    "base_url": "https://api.openai.com/v1",
    "model": "text-embedding-3-small",
    "api_key_required": true,
    "max_tokens": 4096,
    "context_window_tokens": 128000,
    "top_p": null,
    "top_k": null,
    "dimensions": 1536,
    "supports_streaming": false,
    "supports_thinking": false,
    "supports_embeddings": true
  }
]
```

### POST `/api/api-configs`

新建全局 API 配置，并写入 SQLite 的 `api_configs` 表。`provider` 和 `kind` 通常来自模板；`api_key` 可以为空，若 `api_key_required=true` 且未配置 key，该配置不可用于真实 LLM 请求，会触发对应视角的本地降级或聊天请求错误。结构化写作请求运行时固定为非流式 JSON；作品聊天会按请求类型使用流式自由文本。`mode` 当前仍作为兼容字段保存，传入值会被规范化为 `non_stream`。

`max_tokens` 表示单次模型输出 token 预算，允许范围为 `256` 到 `10000000`，会发送给模型 API。`context_window_tokens` 表示模型总上下文窗口，允许范围为 `1024` 到 `10000000`，只用于本地预算检查，不发送给供应商。真实请求进入模型前由后端检查 `输入 token 估算 + max_tokens <= context_window_tokens`，Prompt Preview 同步展示该预算；超出时返回 `llm_context_window_exceeded`，用户需要减少素材、最近章节、聊天历史或输出预算。

请求：

```json
{
  "name": "DeepSeek 正式",
  "provider": "deepseek",
  "kind": "llm",
  "protocol": "openai_compatible",
  "base_url": "https://api.deepseek.com",
  "api_key": "sk-...",
  "api_key_required": true,
  "mode": "non_stream",
  "model": "deepseek-v4-pro",
  "thinking_enabled": true,
  "reasoning_effort": "max",
  "max_tokens": 2048,
  "context_window_tokens": 1000000,
  "temperature": null,
  "top_p": 0.9,
  "top_k": 40,
  "dimensions": null,
  "is_default": false
}
```

### PUT `/api/api-configs/{config_id}`

更新全局 API 配置。`api_key` 留空或传 `null` 表示不改变已保存 key；`clear_api_key=true` 表示清除该配置里的 key。`kind` 创建后不可修改，不能把 LLM 配置改成 Embedding，也不能把 Embedding 改成 LLM；需要更换类型时必须新建配置。
`max_tokens` 和 `context_window_tokens` 的允许范围与创建接口一致。

### DELETE `/api/api-configs/{config_id}`

删除全局 API 配置。被任何视角引用的配置不能删除；每个 `kind` 的最后一套配置不能删除。若被项目请求配置 `prompt_profiles.config.api_config_id` 引用，删除时后端会在同一事务中清理这些请求级引用字段，保留其它 config 字段，使对应请求后续回退到默认 LLM 配置。

### PUT `/api/api-configs/{config_id}/default`

将指定配置设为默认配置。默认配置按 `kind` 隔离：可以同时有一套默认 LLM 配置和一套默认 Embedding 配置。

### POST `/api/api-configs/{config_id}/health-check`

测试指定全局 API 配置是否可被本软件真实使用。该接口不依赖小说项目；真实 LLM 或 Embedding 请求会进入 `ModelRequestQueueService` 统一模型队列，但不写 Debug 请求日志，也不累计 Token usage。

LLM 配置会走 OpenAI SDK Chat Completions，并复用真实写作请求的运行参数：`base_url`、`api_key_required`、`model`、`max_tokens`、`temperature`、`top_p`、`top_k`、DeepSeek thinking 和 SiliconFlow thinking 扩展。请求仍然强制 `stream=false` 和 `response_format.type=json_object`，并要求模型返回 `{"text":"ok"}` 形态的 JSON object。

健康检查只验证结构化写作链路的 JSON 能力；作品聊天的流式自由文本不单独做健康检查。

Embedding 配置会走 OpenAI-compatible embeddings endpoint，发送短文本 `ping`；若配置了 `dimensions`，健康检查会携带该参数并校验实际返回向量维度。

响应：

```json
{
  "ok": true,
  "config_id": "default-api",
  "kind": "llm",
  "provider": "deepseek",
  "model": "deepseek-v4-pro",
  "mode": "non_stream",
  "latency_ms": 482,
  "checked_at": "2026-04-26T08:00:00+00:00",
  "json_mode_supported": true,
  "embedding_dimensions": null,
  "error_code": null,
  "error_message": null
}
```

失败时仍返回 200 和 `ok=false`，前端应展示 `error_message` 的摘要。响应不会包含 API Key、Authorization header 或原始 request body。

## Generation

续写、快速生成、润色、章节铺设和资料生成弹窗的预设分八组：`writing_mode`、`quick_generation_mode`、`chapter_blueprint_mode`、`author_persona`、`polish_mode`、`document_polish_mode`、`document_generation_mode` 和 `editor_persona`。默认内容来自 `backend/config/generation.yaml`；用户在某本小说里的新增、改名、正文修改和删除都会写入 SQLite 的 `generation_presets`，只影响当前项目，不改 YAML。所有真实模型请求都会进入 `ModelRequestQueueService` 统一模型队列，避免和视角建议或健康检查互相挤爆供应商并发。

### GET `/api/projects/{project_id}/generation/presets`

读取当前项目可用的生成预设。后端会先读取 YAML 默认，再用项目数据库覆盖同名默认；被项目删除过的默认预设会被隐藏。

响应：

```json
{
  "writing_modes": [
    {
      "id": "camera",
      "kind": "writing_mode",
      "name": "镜头写作",
      "content": "以镜头语言续写...",
      "is_system": true,
      "is_hidden": false,
      "created_at": null,
      "updated_at": null
    }
  ],
  "quick_generation_modes": [],
  "chapter_blueprint_modes": [],
  "author_personas": [],
  "polish_modes": [],
  "document_polish_modes": [],
  "document_generation_modes": [],
  "editor_personas": []
}
```

### POST `/api/projects/{project_id}/generation/presets`

新增项目级预设。

请求：

```json
{
  "kind": "writing_mode",
  "name": "倒叙写作",
  "content": "从结果反推原因，但不要提前解释谜底。"
}
```

### PUT `/api/projects/{project_id}/generation/presets/{kind}/{preset_id}`

更新项目级预设，或覆盖 YAML 默认预设在当前项目中的名称/内容。只传要更新的字段即可。

请求：

```json
{
  "content": "项目自己的镜头写作提示词。"
}
```

### DELETE `/api/projects/{project_id}/generation/presets/{kind}/{preset_id}`

删除项目级预设；如果目标是 YAML 默认预设，则在当前项目里写入隐藏标记，不改动 YAML。

### POST `/api/projects/{project_id}/generation/draft`

生成续写正文。前端会把正文光标位置和光标前后最近的非空段落一起提交，后端在提示词中明确说明 `text` 会插入到 `previous_paragraph` 与 `next_paragraph` 之间。后端会经由 `ModelRequestQueueService` 用非流式 JSON 请求模型，并要求响应通过强制 schema：顶层只能包含非空字符串 `text`。校验通过后，`text` 才会作为可直接放进正文的文本返回；配置不可用或模型调用失败时返回 `source=local` 的本地兜底文本。

请求：

```json
{
  "chapter_id": "chapter-001",
  "action": "next_paragraph",
  "cursor_index": 1280,
  "previous_paragraph": "林澈停在码头边，雨水顺着袖口往下滴。",
  "next_paragraph": "远处的巡逻艇忽然关掉了探照灯。",
  "writing_preset_id": "camera",
  "writing_prompt": "使用镜头语言继续写。",
  "author_preset_id": "skill",
  "author_skill": "保持冷静克制。"
}
```

响应：

```json
{
  "text": "他没有马上回头，只把录音笔按得更紧。",
  "source": "llm",
  "model": "deepseek-v4-pro"
}
```

### POST `/api/projects/{project_id}/generation/quick-draft`

快速生成下一段正文。该接口用于正文框聚焦时的 `Tab` 快速生成，前端会使用已保存的 `author_persona` 配置，并把正文光标位置、光标前最近段落和光标后第一段正文提交给后端。后端使用请求管理里的 `quick_generate_next_paragraph` 模板、模型配置和 Temperature；右侧栏的 Tab 快速生成模型选择、Temperature、System 提示词、User 提示词和执笔作者人格也直接读写同源配置，因此会持久化到 SQLite，并与请求管理弹窗保持内容统一。System/User 提示词中的 `{input.*}` 占位符仍由后端统一 renderer 渲染，后端仍会追加不可删除的 JSON 输出契约。`quick_preset_id` 和 `quick_prompt` 仅作为兼容字段保留；当前后端不会把 `quick_prompt` 或 `quick_generation_prompt` 作为快速生成任务提示词注入最终 prompt。真实请求经由 `ModelRequestQueueService` 请求模型；响应仍然必须是 JSON object，顶层只能包含非空字符串 `text`。前端收到后直接插入光标位置并保存，不再进入待确认高亮。

请求：

```json
{
  "chapter_id": "chapter-001",
  "cursor_index": 1280,
  "previous_paragraph": "林澈停在码头边，雨水顺着袖口往下滴。",
  "next_paragraph": "远处的巡逻艇忽然关掉了探照灯。",
  "quick_preset_id": "quick-next-paragraph",
  "quick_prompt": "",
  "author_preset_id": "skill",
  "author_skill": "保持冷静克制。"
}
```

Temperature 不在 `quick-draft` 请求体里传递；它由 `quick_generate_next_paragraph.config.temperature` 读取。空值表示沿用最终 API 配置里的 Temperature；数值会覆盖该请求最终 API 配置里的 Temperature。

响应：

```json
{
  "text": "他抬起手，示意身后的警员先别出声。",
  "source": "llm",
  "model": "deepseek-v4-pro"
}
```

### POST `/api/projects/{project_id}/generation/chapter-blueprint`

为当前章节生成“写作白皮书铺设”要点。前端在正文悬浮球点击“基础铺设”后打开弹窗，并冻结当前正文光标位置；用户选择 `chapter_blueprint_mode` 和 `author_persona`，后端用请求管理里 `generate_chapter_blueprint` 的模板和模型配置组装结构化上下文，并经由 `ModelRequestQueueService` 请求模型。响应必须通过强制 schema：顶层只能包含 `points`，每条是非空写作要点，不能包含编号、固定前缀、外层 `「」` 或 Markdown；前端采纳时只为每条内容加上外层 `「」` 并插入正文光标位置。

请求：

```json
{
  "chapter_id": "chapter-001",
  "cursor_index": 1280,
  "previous_paragraph": "少年靠在哨塔阴影里，银针停在指间。",
  "next_paragraph": "远处巡逻队的脚步声越来越近。",
  "blueprint_preset_id": "basic-blueprint",
  "blueprint_prompt": "铺设本章开场目标、冲突、伏笔和收束钩子。",
  "author_preset_id": "skill",
  "author_skill": "冷静克制，重视动作和线索递进。"
}
```

响应：

```json
{
  "points": [
    "先用一个可见动作交代主角本章目标，避免用旁白解释动机。",
    "中段释放一条可被后文追踪的异常细节，并让它影响当场选择。"
  ],
  "source": "llm",
  "model": "deepseek-v4-pro"
}
```

### POST `/api/projects/{project_id}/generation/polish`

润色选中文本。后端会经由 `ModelRequestQueueService` 用非流式 JSON 请求模型，并要求响应通过强制 schema：顶层只能包含非空字符串 `text`。校验通过后，`text` 才会作为可直接替换选区的文本返回；配置不可用或模型调用失败时返回 `source=local` 的本地兜底文本。

请求：

```json
{
  "chapter_id": "chapter-001",
  "selected_text": "林澈停在门口。",
  "polish_preset_id": "tighten",
  "polish_prompt": "保持克制，增强画面。"
}
```

响应：

```json
{
  "text": "林澈停在门口，听见潮声从楼梯下方漫上来。",
  "source": "llm",
  "model": "deepseek-v4-pro"
}
```

### POST `/api/projects/{project_id}/generation/documents/polish`

润色资料文档选区。后端会用资料润色提示词、资料编辑人格和请求管理里该请求类型的模板及模型配置组装非流式 JSON 请求，并经由 `ModelRequestQueueService` 进入供应商请求；响应必须通过强制 schema：顶层只能包含非空字符串 `text`，其内容应是可直接替换选区的 Markdown 片段。

请求：

```json
{
  "document_id": "outline",
  "chapter_id": "chapter-001",
  "selected_text": "- 林澈回到港口。",
  "polish_preset_id": "document-tighten",
  "polish_prompt": "让资料更清晰。",
  "editor_preset_id": "structured-editor",
  "editor_skill": "保持 Markdown 列表格式。"
}
```

### POST `/api/projects/{project_id}/generation/documents/continue`

为资料文档生成后续内容。后端会读取当前资料全文或截断摘录，结合资料生成提示词、资料编辑人格和请求配置素材，经由 `ModelRequestQueueService` 请求模型返回通过强制 schema 的 `{ "text": "..." }`，并把 `text` 作为可追加到资料末尾的 Markdown 片段。

请求：

```json
{
  "document_id": "outline",
  "chapter_id": "chapter-001",
  "generation_preset_id": "document-continue",
  "generation_prompt": "补充录音笔线索。",
  "editor_preset_id": "structured-editor",
  "editor_skill": "保持结构化记录。"
}
```

资料生成接口里的 `chapter_id` 可为空；传入时仅用于读取该章节标题和本章写作梗概，不会把整章正文作为资料生成上下文。生成类接口如果模型返回 JSON 但不符合 schema，会返回 `502`，并写入 Debug 请求 Log。正文和资料生成校验 `text`，章节基础铺设校验 `points`：

```json
{
  "detail": "LLM response schema validation failed for generate_next_paragraph: text: Value error, text must be a non-empty string",
  "code": "llm_response_schema_error"
}
```

前端应展示错误并允许用户修改提示词后重试；不能显示采纳按钮。

## Chat

作品聊天是当前唯一允许流式 + 非 JSON 的 LLM 请求。它仍然按小说项目隔离，使用 `chat_about_work` 请求配置、全局 LLM API 配置、`ModelRequestQueueService` 和 Debug Log。所有聊天会话接口都会先校验 `project_id` 指向存在且未删除的项目；项目不存在时返回项目级 `404`。后端会先用 `PromptProfileService` 渲染最终 System/User 和 Context Pack，再追加对话历史；真实请求体为 `stream=true`，不会携带 `response_format`，也不会做结构化 schema 校验。

### GET `/api/projects/{project_id}/chat/sessions`

读取当前项目的聊天会话列表，按 `updated_at DESC` 排序。

响应：

```json
[
  {
    "id": "chat-session-id",
    "project_id": "silent-harbor",
    "title": "新对话",
    "created_at": "2026-04-30T12:00:00+00:00",
    "updated_at": "2026-04-30T12:10:00+00:00"
  }
]
```

### POST `/api/projects/{project_id}/chat/sessions`

新建聊天会话。

请求：

```json
{
  "title": "设定讨论"
}
```

响应为会话详情，`messages` 初始为空。

### GET `/api/projects/{project_id}/chat/sessions/{session_id}`

读取会话详情和消息。消息按 `created_at, id` 排序，保证同一轮用户消息和助手消息顺序稳定。

响应：

```json
{
  "id": "chat-session-id",
  "project_id": "silent-harbor",
  "title": "设定讨论",
  "created_at": "2026-04-30T12:00:00+00:00",
  "updated_at": "2026-04-30T12:10:00+00:00",
  "messages": [
    { "role": "user", "content": "这章后面怎么推进？" },
    { "role": "assistant", "content": "可以先让线索落到一个可见动作上。", "reasoning": "" }
  ]
}
```

### PATCH `/api/projects/{project_id}/chat/sessions/{session_id}`

重命名聊天会话。

请求：

```json
{
  "title": "码头线索讨论"
}
```

### DELETE `/api/projects/{project_id}/chat/sessions/{session_id}`

删除当前项目内的一个聊天会话及其消息。前端必须提供确认交互。

### POST `/api/projects/{project_id}/chat`

发起一次流式作品聊天。响应为 `text/event-stream`。

请求：

```json
{
  "chapter_id": "chapter-001",
  "session_id": "chat-session-id",
  "messages": [
    { "role": "user", "content": "这章后面怎么推进？" }
  ]
}
```

SSE 事件：

```text
data: {"delta":"可以先","reasoning_delta":""}

data: {"delta":"让线索落到动作上。","reasoning_delta":""}

data: [DONE]
```

`delta` 是助手回复正文增量，`reasoning_delta` 是兼容 DeepSeek 等供应商的推理增量。模型流结束后，若提供 `session_id`，后端会先把用户消息和聚合后的助手消息写入 `chat_messages`，并更新 `chat_sessions.updated_at`；只有持久化成功后才发送 `data: [DONE]`。如果会话不存在或保存失败，流不会伪装成成功完成。Debug Log 保存实际 `stream=true` request body、聚合文本、推理文本、原始 stream chunks 和供应商 usage；若供应商没有返回 usage，则计入 unknown usage。

## Chapters

### GET `/api/projects/{project_id}/chapters`

读取项目章节列表。

### GET `/api/projects/{project_id}/chapters/tree`

读取章节目录树。旧项目里的扁平章节会自动迁移为根级 `chapter` 节点。

响应：

```json
[
  {
    "id": "volume-1",
    "parent_id": null,
    "type": "folder",
    "title": "第一卷",
    "chapter_id": null,
    "word_count": 0,
    "updated_at": "2026-04-26T00:00:00+00:00",
    "children": [
      {
        "id": "chapter-001",
        "parent_id": "volume-1",
        "type": "chapter",
        "title": "第一章 雾里的人",
        "chapter_id": "chapter-001",
        "word_count": 3200,
        "updated_at": "2026-04-26T00:00:00+00:00",
        "children": []
      }
    ]
  }
]
```

### GET `/api/projects/{project_id}/chapters/search`

旧章节搜索接口，仅搜索章节标题和正文。新前端统一使用 `GET /api/projects/{project_id}/search`；该接口保留给内部兼容和窄范围章节搜索。后端使用 SQLite FTS5 维护章节全文索引；三字及以上查询走 trigram FTS，短词查询走索引表内的 `LIKE` fallback，不在每次搜索时扫描章节文件。

查询参数：

- `q`：搜索词。
- `scope_node_id`：可选，限制在某个章节目录及其子节点下搜索。
- `limit=30`：结果上限，最大 50。

响应：

```json
{
  "query": "港口改造",
  "results": [
    {
      "chapter_id": "chapter-001",
      "node_id": "chapter-001",
      "title": "第一章 雾里的人",
      "path": ["第一卷"],
      "word_count": 3200,
      "score": -0.8,
      "matches": [
        {
          "field": "content",
          "snippet": "真正的失踪原因与<mark>港口改造</mark>计划相连。"
        }
      ]
    }
  ]
}
```

### POST `/api/projects/{project_id}/chapters/export-docx`

导出选中章节的正文为 `.docx` 文档。该接口只导出可阅读正文，不包含资料、提示词、Debug 日志或项目备份 manifest；它和项目 zip 导出不是同一功能。

请求：

```json
{
  "chapter_ids": ["chapter-001", "chapter-002"]
}
```

响应类型为 `application/vnd.openxmlformats-officedocument.wordprocessingml.document`。后端会按章节目录树维护的阅读顺序输出章节，即使前端传入的 `chapter_ids` 顺序不同也不会打乱正文顺序；每章以章节标题开头，多章之间插入分页。

### POST `/api/projects/{project_id}/chapters/nodes`

新建章节目录或章节。目录节点只写 SQLite；章节节点会同时创建章节正文文件、`chapters` 元数据、目录节点和搜索索引。

请求：

```json
{
  "type": "chapter",
  "title": "港口线索",
  "parent_id": "volume-1",
  "content": ""
}
```

### PATCH `/api/projects/{project_id}/chapters/nodes/{node_id}`

重命名章节目录或章节。章节节点重命名会同步更新 `chapters.title` 和搜索索引标题。

### PATCH `/api/projects/{project_id}/chapters/nodes/{node_id}/move`

移动章节目录或章节。`parent_id=null` 表示移动到根目录；`before_node_id=null` 表示放到目标目录末尾。目标父节点必须是目录，后端会禁止把目录移动到自己的子孙节点内，并统一重算同级 `chapter_nodes.order_index`。章节树变更后，后端还会按目录树前序遍历重建 `chapters.order_index`，保证最近 N 章、默认章节和阅读顺序都与目录一致。

请求：

```json
{
  "parent_id": "volume-1",
  "before_node_id": "chapter-002"
}
```

响应：

```json
{
  "chapter_tree": [],
  "chapters": []
}
```

### DELETE `/api/projects/{project_id}/chapters/nodes/{node_id}`

删除章节目录或章节。目录会递归删除子目录和章节；章节正文文件会移动到 `backend/data/trash/{project_id}/chapter-nodes/` 下，并写入 `manifest.json`。后端会同步清理 `chapters` 元数据、目录节点和全文搜索索引。为了保证工作台始终有可打开章节，后端不允许删除最后一个章节。

### POST `/api/projects/{project_id}/chapters`

新增根级章节。服务层会分配章节 ID、追加顺序、写入章节文件、创建根级章节节点并更新搜索索引。

请求：

```json
{
  "title": "第二章 旧警署",
  "content": "",
  "parent_id": null
}
```

### GET `/api/projects/{project_id}/chapters/{chapter_id}`

读取章节正文。

响应包含：

```json
{
  "id": "chapter-001",
  "title": "第一章 雾里的人",
  "order": 1,
  "word_count": 3200,
  "content": "章节正文",
  "writing_synopsis": "本章写港口旧案重新浮出水面。",
  "writing_synopsis_updated_at": "2026-04-26T00:00:00+00:00",
  "updated_at": "2026-04-26T00:00:00+00:00"
}
```

### PUT `/api/projects/{project_id}/chapters/{chapter_id}`

保存章节正文。服务层会更新章节字数、章节节点更新时间、项目更新时间和全文搜索索引。

请求：

```json
{
  "content": "新的章节正文",
  "base_updated_at": "2026-04-26T00:00:00+00:00"
}
```

`base_updated_at` 可为空；传入时表示客户端基于哪个章节版本保存。该字段是后端返回的 `updated_at` 不透明字符串，客户端必须原样回传最近一次 GET / 保存响应中的值，不得重新格式化或自行生成。若服务端当前 `updated_at` 已变化，返回 `409`，前端不得把该章节标记为已保存。保存成功响应会在章节详情外额外返回 `project` 摘要，前端应以后端 `project.updated_at` / `project.word_count` 为准。保存后，后端会根据 `/api/version-settings` 的策略判断是否为该章节写入一个 `auto` 历史版本。

### PUT `/api/projects/{project_id}/chapters/{chapter_id}/writing-synopsis`

保存章节右侧栏的写作梗概。该接口只更新 `writing_synopsis`、`writing_synopsis_updated_at`、章节节点更新时间和项目更新时间，不更新章节正文 `updated_at`，也不会触发章节正文自动版本。

请求：

```json
{
  "writing_synopsis": "本章写港口旧案重新浮出水面。",
  "base_updated_at": "2026-04-26T00:00:00+00:00"
}
```

`base_updated_at` 对应最近一次响应里的 `writing_synopsis_updated_at`，可为空；不为空时用于梗概自己的乐观锁。若服务端梗概已被其它窗口保存，返回 `409`。响应形状与章节详情一致，并额外包含 `project` 摘要。

## Versions

### GET `/api/projects/{project_id}/versions`

读取某个章节或资料文本的历史版本。

查询参数：

- `resource_type`：`chapter` 或 `document`。
- `resource_id`：章节 ID 或资料节点 ID。

### POST `/api/projects/{project_id}/versions`

为当前章节或资料文本创建一个手动历史版本。

请求：

```json
{
  "resource_type": "chapter",
  "resource_id": "chapter-001",
  "version_type": "manual",
  "label": "第一幕定稿",
  "note": "修完主要悬念。"
}
```

### GET `/api/projects/{project_id}/versions/{version_id}`

读取历史版本详情和正文快照。

### POST `/api/projects/{project_id}/versions/{version_id}/restore`

恢复到指定历史版本。恢复前后端会先为当前内容写入 `pre_restore` 版本，再把历史快照写回当前章节或资料文本。

## Perspectives

### GET `/api/projects/{project_id}/perspectives`

读取项目启用和未启用的全部 AI 视角。

### POST `/api/projects/{project_id}/perspectives`

新增当前项目的定制 AI 视角。新建视角默认 `is_enabled=false`，不会参与批量刷新或自动建议；用户仍可在写作台手动刷新该单个视角。

请求：

```json
{
  "name": "节奏编辑",
  "description": "关注段落推进、悬念强度和信息密度。",
  "instructions": "评价当前段落的节奏，指出是否需要加速、停顿或补充更具体的悬念。",
  "api_config_id": null
}
```

### PATCH `/api/projects/{project_id}/perspectives/{perspective_id}`

修改 AI 视角名称、描述、提示词、启用状态或 `api_config_id`。`api_config_id=null` 表示使用默认 LLM API 配置；`api_config_id` 只能引用 `kind=llm` 的配置。

### DELETE `/api/projects/{project_id}/perspectives/{perspective_id}`

删除项目内的 AI 视角。前端应对删除动作做确认。

## Request Profiles

### GET `/api/projects/{project_id}/prompt-profiles`

读取当前项目的请求配置。每类请求都有独立模板、素材选择和请求模型选择，当前请求类型包括：

- `perspective_suggestion`
- `polish_selection`
- `quick_generate_next_paragraph`
- `generate_next_paragraph`
- `generate_next_section`
- `generate_chapter_blueprint`
- `polish_document_selection`
- `generate_document_continuation`
- `chat_about_work`

章节素材支持两种模式：

- `chapter_ids`：固定章节，按项目保存，不随当前写作章节变化。
- `config.recent_chapter_enabled` + `config.recent_chapter_count`：最近 N 章，在请求时根据当前章节顺序动态展开，不包含当前章节本身。

后端组装请求时会先展开最近 N 章，再追加固定章节，并按顺序去重。资料素材仍由 `document_ids` 固定勾选。`config` 还可保存 `max_item_chars`、`max_material_chars` 等素材截断上限；`config.api_config_id` 可指定该请求类型使用的 LLM API 配置，不填时使用默认 LLM 配置；`config.temperature` 可指定该请求类型的 Temperature，空值表示继承最终 API 配置。保存请求配置时，`config.api_config_id` 必须引用存在的 `kind=llm` 配置；空白值会被清理，不存在或 Embedding 配置会返回 404。`config.temperature` 必须是 0 到 2 之间的数字，空白值会被清理。视角建议仍允许单个视角覆盖自己的 `api_config_id`；没有视角级配置时才使用请求配置；Temperature 始终来自 `perspective_suggestion` 请求配置。

### PUT `/api/projects/{project_id}/prompt-profiles/{request_type}`

更新指定请求类型的请求配置。

请求：

```json
{
  "name": "生成下一段落",
  "system_template": "你是小说正文续写助手。",
  "output_contract": "最终响应必须只返回合法 JSON object，顶层只能包含 text。",
  "user_template": "最近正文：{input.current_chapter}\n相关章节：{input.chapters}",
  "chapter_ids": ["chapter-001"],
  "document_ids": ["outline"],
  "config": {
    "recent_chapter_enabled": true,
    "recent_chapter_count": 2,
    "include_chapter_synopsis": true,
    "api_config_id": "deepseek-v4-flash",
    "temperature": 0.7,
    "max_item_chars": 20000,
    "max_material_chars": 120000
  }
}
```

`system_template`、`user_template`、`output_contract`、有效的 `config.api_config_id` 和有效的 `config.temperature` 都会保存到当前项目的请求配置；最终 System message 会按顺序拼接渲染后的 `system_template` 与 `output_contract`。结构化写作请求的 `output_contract` 是强制 JSON 契约；`chat_about_work` 的 `output_contract` 是流式自由文本对话约定，不要求 JSON。`config.include_chapter_synopsis` 控制是否把当前请求章节的 `writing_synopsis` 注入 `Context Pack focus`，缺省为 `true`；开启时只读取当前 `chapter_id` 对应的本章梗概，不读取其它章节梗概。常用占位符包括 `{input.context_pack}`、`{input.materials}`、`{input.agents}`、`{input.chapters}`、`{input.documents}`、`{input.blueprint_prompt}`；旧占位符 `{input.textures}` 继续兼容并等价于资料素材。快速生成不再提供 `{input.quick_prompt}` 任务提示词入口。

首次保存某个 `project_id + request_type` 时，后端会先把当前有效配置写为 `initial` 版本，再写入新的 `manual` 版本。后续每次保存都会生成 `manual` 版本；恢复历史版本前会先生成 `pre_restore` 备份。

### GET `/api/projects/{project_id}/prompt-profiles/{request_type}/versions`

读取指定请求配置的历史版本列表，按创建时间倒序返回。列表项包含版本类型、名称、时间和快照摘要字数，不直接返回完整模板正文。

响应：

```json
[
  {
    "id": "prompt-generate_next_paragraph-manual-abc123",
    "project_id": "silent-harbor",
    "request_type": "generate_next_paragraph",
    "version_type": "manual",
    "label": "生成下一段落默认模板",
    "note": "用户保存请求配置。",
    "system_chars": 128,
    "user_chars": 512,
    "chapter_count": 2,
    "document_count": 1,
    "created_at": "2026-04-26T08:00:00+00:00"
  }
]
```

### GET `/api/projects/{project_id}/prompt-profiles/{request_type}/versions/{version_id}`

读取单个请求配置历史版本的完整快照。`snapshot` 包含 `name`、`system_template`、`user_template`、`output_contract`、`chapter_ids`、`document_ids` 和 `config`。

### POST `/api/projects/{project_id}/prompt-profiles/{request_type}/versions/{version_id}/restore`

恢复指定请求配置版本。恢复前后端会把当前配置写为 `pre_restore` 版本，然后用快照覆盖当前 `prompt_profiles` 记录。该接口只影响当前项目的当前请求类型，不影响其他项目或其他请求类型。

响应：

```json
{
  "profile": {
    "request_type": "generate_next_paragraph",
    "name": "生成下一段落默认模板",
    "system_template": "你是小说正文续写助手。",
    "user_template": "最近正文：{input.current_chapter}",
    "output_contract": "强制输出契约...",
    "chapter_ids": [],
    "document_ids": ["outline"],
    "config": {
      "recent_chapter_enabled": true,
      "recent_chapter_count": 2
    },
    "is_system": false,
    "created_at": "2026-04-26T08:00:00+00:00",
    "updated_at": "2026-04-26T09:00:00+00:00"
  },
  "version": {
    "id": "prompt-generate_next_paragraph-manual-abc123",
    "project_id": "silent-harbor",
    "request_type": "generate_next_paragraph",
    "version_type": "manual",
    "label": "生成下一段落默认模板",
    "note": "用户保存请求配置。",
    "system_chars": 128,
    "user_chars": 512,
    "chapter_count": 0,
    "document_count": 1,
    "created_at": "2026-04-26T08:00:00+00:00",
    "snapshot": {
      "name": "生成下一段落默认模板",
      "system_template": "你是小说正文续写助手。",
      "user_template": "最近正文：{input.current_chapter}",
      "output_contract": "强制输出契约...",
      "chapter_ids": [],
      "document_ids": ["outline"],
      "config": {
        "recent_chapter_enabled": true,
        "recent_chapter_count": 2
      }
    }
  }
}
```

## Request Preview

### POST `/api/projects/{project_id}/prompt-preview`

Dry Run 预览某类 LLM 请求的最终提示词。该接口只读，不调用 LLM，不写 Debug 请求日志，不消耗 Token。后端会复用正式请求的 `PromptProfileService` 拼装逻辑，因此预览中的 System/User、结构化 Context Pack、最近 N 章展开结果和素材截断规则应与真实请求一致。

响应里的 `token_estimate` 是对最终 System/User 消息的粗略输入 Token 估算，用于在请求管理界面掌控上下文长度；它不来自供应商真实 usage，也不会计入 Token 统计。中文字符按接近 1 字 1 token 估算，英文和符号按长度折算，因此不同模型 tokenizer 下会有少量偏差。

`context_pack` 是后端在渲染 User message 前生成的结构化上下文对象，包含 `task`、`project`、`focus`、`materials`、`agents`、`constraints` 和分块 token 估算。最终发给模型的原始 System/User 仍以 `messages` 为准；`context_pack` 用于 Dry Run、Debug 和上下文预算检查，不会被写进供应商原始 request body 的额外字段。

当 `request_type=chat_about_work` 时，预览展示的是聊天请求前置的 System/User 和上下文包；真实请求会在这些消息后追加当前对话历史，并以 `stream=true` 发送，不携带 `response_format`。

`focus[].key` 使用语义化名称，避免不同请求类型共用含糊字段：章节摘录统一为 `chapter_excerpt`，资料摘录为 `document_excerpt`，小说选区为 `selected_chapter_text`，资料选区为 `selected_document_text`，小说润色提示为 `chapter_polish_prompt`，资料润色提示为 `document_polish_prompt`，资料续写提示为 `document_generation_prompt`。当请求配置的 `include_chapter_synopsis` 开启且请求携带章节上下文时，`focus` 会包含 `chapter_synopsis`，内容只来自当前章节的写作梗概。正文生成、快速生成和章节基础铺设都包含 `insertion_point`、`previous_paragraph` 和 `next_paragraph`，明确本次结果发生在正文光标位置，结果会插入到前后段之间，而不是默认追加到章节末尾或章节头部；快速生成不再额外注入 `quick_generation_prompt` 任务提示词块，章节基础铺设额外使用 `insertion_target` 和 `blueprint_mode_prompt`，明确程序只为 points 添加外层 `「」`。这些是 Context Pack 的诊断字段名；模板占位符仍兼容 `{input.current_chapter}`、`{input.current_document}`、`{input.selected_text}` 等旧名称。

请求：

```json
{
  "request_type": "generate_next_paragraph",
  "chapter_id": "chapter-003",
  "document_id": null,
  "paragraph": "当前段落",
  "selected_text": "",
  "cursor_index": 1280,
  "previous_paragraph": "林澈停在码头边，雨水顺着袖口往下滴。",
  "next_paragraph": "远处的巡逻艇忽然关掉了探照灯。",
  "writing_prompt": "使用镜头语言继续写。",
  "quick_prompt": "",
  "author_persona_id": "skill",
  "author_persona_name": "冷静克制的悬疑作者",
  "author_persona": "保持冷静克制。",
  "polish_prompt": "",
  "generation_prompt": "",
  "blueprint_prompt": "",
  "editor_persona_id": "",
  "editor_persona_name": "",
  "editor_persona": "",
  "profile_override": {
    "system_template": "你是小说正文续写助手。",
    "user_template": "最近正文：{input.current_chapter}",
    "chapter_ids": ["chapter-001"],
    "document_ids": ["outline"],
    "config": {
      "recent_chapter_enabled": true,
      "recent_chapter_count": 2
    }
  }
}
```

`profile_override` 只用于本次预览，不写数据库，主要供请求管理弹窗预览未保存改动。

响应：

```json
{
  "request_type": "generate_next_paragraph",
  "items": [
    {
      "label": "生成下一段落",
      "api_config": {
        "id": "default-api",
        "name": "默认 API 配置",
        "provider": "deepseek",
        "kind": "llm",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
        "api_key_required": true,
        "api_key_configured": true,
        "configured": true,
        "is_default": true,
        "context_window_tokens": 1000000
      },
      "token_estimate": {
        "input_tokens": 2100,
        "system_tokens": 520,
        "user_tokens": 1570,
        "output_token_budget": 4096,
        "total_with_output_budget": 6196,
        "context_window_tokens": 1000000,
        "context_usage_ratio": 0.006196,
        "context_window_exceeded": false,
        "estimator": "rough_mixed_text"
      },
      "context_pack": {
        "version": 1,
        "request_type": "generate_next_paragraph",
        "project_id": "silent-harbor",
        "task": "基于正文光标前后的段落边界、写作方式和素材，生成一段可直接插入光标位置的中文小说文本。",
        "project": {
          "title": "静默港",
          "genre": "悬疑"
        },
        "focus": [
          {
            "key": "insertion_point",
            "label": "正文生成插入点",
            "format": "json",
            "content": "{\n  \"cursor_index\": 1280,\n  \"previous_paragraph_key\": \"previous_paragraph\",\n  \"next_paragraph_key\": \"next_paragraph\",\n  \"rule\": \"本次生成的 text 会插入在 previous_paragraph 之后、next_paragraph 之前；next_paragraph 为空表示光标后没有正文段落。\"\n}",
            "content_mode": "full",
            "chars": 180,
            "token_estimate": 120,
            "empty": false,
            "metadata": {}
          },
          {
            "key": "previous_paragraph",
            "label": "光标前最近的有文字段落",
            "format": "plain",
            "content": "林澈停在码头边，雨水顺着袖口往下滴。",
            "content_mode": "full",
            "chars": 21,
            "token_estimate": 21,
            "empty": false,
            "metadata": {}
          },
          {
            "key": "next_paragraph",
            "label": "光标后第一段正文",
            "format": "plain",
            "content": "远处的巡逻艇忽然关掉了探照灯。",
            "content_mode": "full",
            "chars": 17,
            "token_estimate": 17,
            "empty": false,
            "metadata": {"optional": true}
          },
          {
            "key": "chapter_excerpt",
            "label": "当前章节末尾摘录",
            "format": "plain",
            "content": "...",
            "content_mode": "tail",
            "chars": 7000,
            "token_estimate": 1800,
            "empty": false,
            "metadata": {}
          }
        ],
        "materials": [
          {
            "id": "outline",
            "title": "基本蓝图",
            "kind": "document",
            "source": "fixed",
            "format": "markdown",
            "content": "# 基本蓝图\n...",
            "content_mode": "full",
            "chars": 1200,
            "token_estimate": 420,
            "truncated": false
          }
        ],
        "agents": [],
        "constraints": ["最终响应必须遵守系统消息中的强制 JSON 输出契约。"],
        "budget": {
          "input_tokens": 2600,
          "task_tokens": 40,
          "project_tokens": 20,
          "focus_tokens": 1800,
          "material_tokens": 420,
          "agent_tokens": 0,
          "truncated_materials": 0,
          "estimator": "rough_mixed_text"
        }
      },
      "request_options": {
        "max_tokens": 4096,
        "response_format": { "type": "json_object" },
        "stream": false,
        "mode": "non_stream"
      },
      "messages": [
        { "role": "system", "content": "..." },
        { "role": "user", "content": "..." }
      ],
      "chapters": [
        {
          "id": "chapter-002",
          "title": "第二章",
          "source": "recent",
          "chars": 3200,
          "truncated": false,
          "kind": "chapter",
          "format": "plain",
          "content_mode": "full",
          "token_estimate": 900
        }
      ],
      "documents": [],
      "warnings": []
    }
  ],
  "warnings": []
}
```

视角建议按启用视角逐个返回 `items`，即使多个视角使用同一套 API 配置，也会展示为互相独立的预览请求。响应不包含 API Key。LLM 响应必须通过 schema：顶层 `cards` 必须是数组，每张卡只能包含 `perspective_id`、`title`、`body`、可选 `detail` 和 `severity`；`perspective_id` 必须来自本次输入视角且不可重复，`severity` 只能是 `calm`、`focus` 或 `risk`。某个视角的请求返回不合规 schema 时，只影响该视角，并回退为本地建议卡。

## Suggestions

### POST `/api/projects/{project_id}/suggestions`

根据当前段落和项目 AI 视角生成建议卡片。默认不自动调用；前端手动刷新单个视角时会传 `perspective_id`，批量刷新和自动建议模式会为每个已开启视角分别发起单视角请求。

所有请求先进入后端 `SuggestionQueueService` 轻量调度层，再调用 `SuggestionService` 执行真实单视角建议生成。`SuggestionQueueService` 只负责 pending 去重、自动任务替换和 trigger 到模型优先级的映射，不会把多个视角合并进同一个 LLM prompt；真正打到供应商的 Chat Completions 请求会进入 `ModelRequestQueueService` 统一模型队列，由模型队列控制并发和最终执行顺序。

后端会读取：

- 当前章节正文和当前段落。
- 项目基本信息。
- 请求配置中选取的固定章节、最近 N 章和资料素材。
- 当前项目内已启用的 AI 视角及其提示词；如果传入 `perspective_id`，则只读取该视角，且不要求该视角处于开启状态。

如果对应视角选择了可用 LLM API 配置，则服务层会通过 OpenAI Python SDK 请求 OpenAI-compatible Chat Completions，并使用非流式 `response_format.type=json_object` 解析 JSON 卡片。如果某个视角的配置需要 key 但未配置、请求失败或模型输出不可用，只让该视角返回本地规则降级卡片，`source` 会标记为 `local`。

每次建议请求会按视角读取 `api_config_id`；未选择时使用 `perspective_suggestion` 请求配置里的 `config.api_config_id`，仍未选择时使用默认 LLM API 配置。所有目标视角都会独立构造提示词、独立调用 LLM、独立记录 Debug Log 并独立 schema 校验；即使多个视角使用同一配置，也不会合并到同一次请求。`response_format.type=json_object` 始终由后端保留。

队列规则：

- 真实供应商并发由 `ModelRequestQueueService` worker 数控制，避免批量或自动建议一拥而上。
- 请求 key 为 `project_id + chapter_id + perspective_id + paragraph_hash`；相同 key 的 pending 请求会复用同一任务。
- `trigger=manual` 会映射为最高模型优先级，`trigger=batch` 次之，`trigger=auto` 最低。
- 同一章节同一视角的自动建议如果仍在 pending 或等待模型队列，会被更新段落的自动建议取消替换。
- 视角执行单位始终是单视角；批量只表示批量入队，不表示合并请求。

请求：

```json
{
  "chapter_id": "chapter-001",
  "paragraph": "用户刚打出的段落",
  "perspective_id": "pace-editor",
  "trigger": "manual"
}
```

`perspective_id` 可选。省略时后端会请求所有已开启视角；提供时只请求该单个视角，便于前端实现手动单个刷新和互不干扰的并发请求。

`trigger` 可选，默认 `manual`，可选值为 `manual`、`batch`、`auto`，只影响队列调度优先级和自动任务替换策略。

响应：

```json
[
  {
    "id": "a1b2c3d4e5",
    "perspective_id": "pace-editor",
    "perspective_name": "节奏编辑",
    "title": "推进节奏清爽",
    "body": "当前段落长度利于阅读，可以补一个更具象的动作或道具。",
    "severity": "calm",
    "source": "llm",
    "model": "deepseek-v4-pro"
  }
]
```

响应字段：

- `severity`：`calm`、`focus`、`risk`。
- `source`：`llm` 或 `local`。
- `model`：真实 LLM 返回时记录模型名，本地降级时为 `null`。

## Debug

### GET `/api/debug`

读取 Debug 页面需要的 Token 统计和最近 50 次请求 Log。可选 `project_id` 用于限制在单个小说项目内。

响应：

```json
{
  "token_usage": {
    "today": 12000,
    "last_7_days": 58000,
    "last_30_days": 240000,
    "total": 920000,
    "unknown_usage_requests": 0
  },
  "request_logs": [
    {
      "id": "log-id",
      "project_id": "silent-harbor",
      "model_kind": "llm",
      "request_type": "generate_next_paragraph",
      "api_config_id": "default-api",
      "provider": "deepseek",
      "model": "deepseek-v4-pro",
      "status": "success",
      "created_at": "2026-04-26T12:00:00+00:00",
      "request_body": {},
      "response_body": {},
      "debug_readable": {
        "system_messages": [
          {
            "role": "system",
            "content": "系统提示词正文"
          }
        ],
        "user_messages": [
          {
            "role": "user",
            "content": "用户提示词正文"
          }
        ],
        "request_options": {
          "model": "deepseek-v4-pro",
          "stream": false,
          "response_format": {
            "type": "json_object"
          }
        },
        "context_pack": {
          "version": 1,
          "request_type": "generate_next_paragraph",
          "project_id": "silent-harbor",
          "task": "基于正文光标前后的段落边界、写作方式和素材，生成一段可直接插入光标位置的中文小说文本。",
          "project": {},
          "focus": [],
          "materials": [],
          "agents": [],
          "constraints": [],
          "budget": {
            "input_tokens": 2600,
            "task_tokens": 40,
            "project_tokens": 20,
            "focus_tokens": 1800,
            "material_tokens": 420,
            "agent_tokens": 0,
            "truncated_materials": 0,
            "estimator": "rough_mixed_text"
          }
        },
        "context_budget": {
          "input_tokens": 2600,
          "task_tokens": 40,
          "project_tokens": 20,
          "focus_tokens": 1800,
          "material_tokens": 420,
          "agent_tokens": 0,
          "truncated_materials": 0,
          "estimator": "rough_mixed_text"
        },
        "context_materials": [],
        "raw_content": "{\"text\":\"生成结果\"}",
        "parsed_payload": {
          "text": "生成结果"
        },
        "schema_error": null,
        "embedding_summary": {}
      },
      "error_message": null,
      "prompt_tokens": 100,
      "completion_tokens": 40,
      "total_tokens": 140,
      "duration_ms": 1200
    }
  ]
}
```

`model_kind` 区分 `llm` 和 `embedding`。LLM 的 `request_body` 和 `response_body` 保存 Chat Completions 的原始请求 body 与原始返回 body；不会保存 API Key 或 Authorization header，也不会混入 `context_pack` 等本地诊断字段。结构化写作请求的原始请求体应显示 `stream=false` 和 `response_format.type=json_object`；作品聊天请求应显示 `stream=true` 且没有 `response_format`，其 `response_body.chunks` 保存流式原始 chunk。`debug_readable` 是由原始 JSON 和独立保存的 Context Pack 派生出的可读视图，用于 Debug 页面按摘要、Context、System、User、参数、原始请求、原始返回和解析结果分栏展示；其中 System/User 必须来自最终渲染后、实际发送给模型的 `messages`。可读视图会对 `api_key`、`Authorization`、`token`、`secret`、`password` 等字段脱敏。Token 统计优先使用供应商返回的 `usage`，未返回 usage 的请求计入 `unknown_usage_requests`，不混入估算 Token。作品聊天不要求 JSON，因此非 JSON 聊天回复不会产生 schema error。

Embedding 分析请求也进入 Debug，但 `request_body` / `response_body` 是脱敏摘要而不是供应商完整 payload。请求摘要可包含 `model`、`dimensions`、`input_count`、`input_hashes`、`segmentation_mode`、`cache`、`tool_type`、`resource_type`、`resource_id`、`run_id`、`batch_label`、`model_signature_hash`；返回摘要可包含 `embedding_count`、`embedding_dimensions`、`usage`、`duration_ms` 和 `error_type`。Embedding Debug 不保存完整 `input` 文本数组、正文切片、资料片段、标签描述或 `data[].embedding` 向量。Embedding 的 `debug_readable.embedding_summary` 汇总安全字段，`system_messages`、`user_messages`、`context_pack`、`raw_content` 和 `parsed_payload` 保持空值。

### GET `/api/debug/token-usage`

读取 Token 统计。可选 `project_id`。

### GET `/api/debug/request-logs`

读取最近请求 Log。可选 `project_id` 和 `limit`，`limit` 范围为 1 到 50。

### GET `/api/debug/model-queue`

读取当前模型请求队列快照，用于主页面和写作台的队列菜单。该接口只返回排队中和运行中的安全元信息，不返回 prompt、正文、响应体、API Key 或 Authorization header。

响应：

```json
{
  "worker_count": 2,
  "queued_count": 1,
  "running_count": 1,
  "items": [
    {
      "id": "model-request-12",
      "kind": "llm",
      "label": "perspective_suggestion",
      "status": "running",
      "priority": "batch",
      "model": "deepseek-v4-pro",
      "queued_at": "2026-04-28T10:12:30+00:00",
      "started_at": "2026-04-28T10:12:31+00:00"
    },
    {
      "id": "model-request-13",
      "kind": "embedding",
      "label": "api_config_health_embedding",
      "status": "queued",
      "priority": "manual",
      "model": "text-embedding-3-small",
      "queued_at": "2026-04-28T10:12:32+00:00",
      "started_at": null
    }
  ]
}
```

### DELETE `/api/debug/token-usage`

清空 Token 统计。可选 `project_id`。

### DELETE `/api/debug/request-logs`

清空请求 Log。可选 `project_id`。

### DELETE `/api/debug/all`

清空 Token 统计和请求 Log。可选 `project_id`。

## 错误约定

- `404`：项目、章节或资源不存在。
- `409`：项目、章节或视角 ID 已存在；或章节/资料保存的 `base_updated_at` 已落后于服务端当前版本。
- `400`：路径越界、领域参数非法等业务错误。
- `400 / llm_context_window_exceeded`：LLM 请求进入供应商前发现 `input_tokens + max_tokens` 超过 API 配置的 `context_window_tokens`。
- `502 / llm_response_schema_error`：结构化 LLM 响应不符合强制 schema，后端不会把该结果当作可采纳正文或建议。
- `503 / llm_not_configured`：需要真实 LLM 的请求在打开流式响应或调用供应商前发现没有可用 LLM API 配置。
- `422`：FastAPI/Pydantic 入参校验失败。
