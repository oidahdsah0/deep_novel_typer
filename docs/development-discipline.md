# 开发纪律

## 环境

- Python 只能使用 conda 环境 `novel`。
- Python 版本固定为 `3.13`。
- 后端依赖以 `backend/environment.yml` 和 `backend/pyproject.toml` 为准。
- 前端目标架构为 Next 16 App Router。

推荐命令：

```bash
./scripts/dev.sh
```

生产构建：

```bash
./scripts/build.sh
```

生产启动：

```bash
./scripts/start.sh
```


手动启动：

```bash
conda activate novel
cd backend
uvicorn app.APIs.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## Codex 内启动与用户浏览器测试

在 Codex 内做实时调试时，Codex 可以负责启动服务、读取终端日志、执行静态检查、非浏览器健康检查和最小浏览器 smoke。涉及前端交互或视觉变化时，Codex 可用 in-app browser 验证页面是否可打开、关键控件是否渲染、控制台是否有 error / warning；最终视觉回归、复杂路径和真实使用体验仍由用户本人确认，交付说明必须列出建议用户验证的浏览器场景。

最短有效路径固定为：

1. 用项目脚本启动，不要手动拆命令：

```bash
./scripts/dev.sh
```

2. 如果脚本需要安装依赖、绑定本机端口，或 `curl` 本地端口时遇到沙箱网络/监听权限问题，应对同一命令申请提升权限后重试。
3. 等终端明确出现 `Next.js ... Ready` 和 `Uvicorn running on http://127.0.0.1:8000` 后，告知用户在浏览器打开：

```text
http://127.0.0.1:3000/
```

4. 首次 `next dev` 可能很慢。本项目观察到过前端显示命令已启动但实际约 3 分钟后才 Ready；这时不要急着改代码，先继续读终端日志。
5. 如果用户反馈浏览器访问异常，或 `curl` 访问前端超时，先区分三种情况：
   - 端口还没监听：继续等 `Ready`。
   - 端口已监听但 0 字节超时：看 Next 日志和后端请求日志，确认 Server Component 的 API fetch 是否挂住。
   - 页面能打开但按钮请求失败：优先检查 CORS。默认只允许前端 `3000` 和 `3001`，临时开 `3003` 会导致浏览器预检失败，除非同步设置 `NOVEL_TYPER_CORS_ORIGINS`。
6. 生产模式验证优先使用：

```bash
./scripts/build.sh
./scripts/start.sh
```

build 阶段执行 `npm run build` 构建前端，start 阶段用 `next start` 启动生产前端 + uvicorn。适合排除 `next dev` 热更新链路导致的问题，但实时改前端仍应回到 `./scripts/dev.sh`。

生产构建和生产启动必须使用同一组后端地址环境变量。`NEXT_PUBLIC_API_BASE_URL` 是前端构建期变量，只在 `scripts/start.sh` 时设置不会改变已经构建好的客户端包。`scripts/build.sh` 会把本次构建使用的 API Base URL 写入 `.next/novel-api-base-url.txt`，`scripts/start.sh` 会在启动前校验当前地址是否一致；不一致时必须重新构建。

如果用备用端口做生产烟测，应固定成同一组命令，例如：

```bash
BACKEND_PORT=8111 FRONTEND_PORT=3111 ./scripts/build.sh
BACKEND_PORT=8111 FRONTEND_PORT=3111 NOVEL_TYPER_CORS_ORIGINS=http://127.0.0.1:3111,http://localhost:3111 ./scripts/start.sh
```

生产构建前必须停掉正在使用同一个 `.next` 目录的 `next dev` / `next start`。不要在生产服务仍运行时删除或重建 `.next`；否则服务端可能读取到半更新 chunk。`npm run build --prefix frontend` 会先清理 `.next`、`.next-novel-backup` 和 `tsconfig.tsbuildinfo`，再构建并校验 App Page 入口、`page_client-reference-manifest.js` 和 SSR chunk 完整性；如果 `/projects/[projectId]` 这类路由已登记但缺 `page.js` 或 client reference manifest，构建必须失败，不能继续启动。构建备份固定写入 `.next-novel-backup/`，不能放进 `.next` 内。`scripts/start.sh` 会在启动前、启动后和高频后台守护中恢复缺失 chunk 与 App route 文件，避免 Next/Turbopack 生产启动期间出现 `ChunkLoadError`、`MODULE_NOT_FOUND` 或 `client reference manifest` 缺失。
7. 如果 `npm run typecheck --prefix frontend` 报 `.next/types/* 2.ts` 或类似重复类型文件冲突，先运行前端内置的 `clean:next-types`。当前 `dev`、`build` 和 `typecheck` 都已经自动执行这个清理步骤。
8. 如果 `npm run lint --prefix frontend` 出现卡死或长时间无输出，以分段 watchdog 的超时结果为准；不要改回裸 `eslint app features lib scripts eslint.config.mjs` 或 `next lint`。先记录输出里的 `[lint] <chunk>` 名称，再只对该分段或更窄目录复跑定位。只有确认是机器性能或临时环境问题时，才临时提高 `ESLINT_CHUNK_TIMEOUT_MS`。

## 分层规则

- `Utils` 不引用 `Services` 或 `APIs`。
- `Services` 可以引用 `Utils`，但不引用 FastAPI 的 `Request`、`Response`、`HTTPException`。
- `APIs` 可以引用 `Services` 和 `Schemas`，但不直接读写数据库或文件。
- 新业务必须先定义 Service，再暴露 API。
- 小说库元数据必须走 SQLite，正文和资料正文必须走文件存储。

## 模块化硬纪律

这是 rebuild 后最重要的开发纪律。新增功能、修 Bug、补测试和改样式都必须先判断归属模块，再落文件。

- 禁止恢复被拆掉的单体入口：不重建 `frontend/lib/api.ts`、`backend/app/Utils/models.py`、`backend/app/Services/api_config_service.py`、`backend/app/Services/api_config_runtime.py`、`backend/app/Services/prompt_profile_service.py` 或 `backend/tests/test_services.py`。
- 禁止把“临时兼容层”长期保留为公共入口。迁移期可以短暂 re-export，但同一阶段收口时必须删除或写明保留理由。
- 新文件必须放在最窄领域目录里。能放 `features/workspace/components/prompts/` 的，不放 `features/workspace/` 根目录；能放 `Services/prompt_profiles/materials.py` 的，不塞回 `service.py`。
- 新逻辑先拆纯函数，再接状态和副作用。可复用、无 I/O、无 React state 的代码必须优先进入 utils / helper 模块。
- 页面、Service、Hook、CSS 文件接近纪律线时，不继续堆逻辑；先拆子组件、hook、repository 或纯函数。
- 每次新增目录、模块边界、数据流或 API 合约，都必须同步更新 `docs/architecture.md`、`docs/development-discipline.md` 或 `docs/backend-api.md` 中对应部分。

落文件决策：

- 前端路由入口：`frontend/app/...`，只做路由、Server Component fetch 或 feature client re-export。
- 前端页面实现：`frontend/features/<domain>/<Domain>Client.tsx`。
- 前端副作用和业务动作：`frontend/features/<domain>/hooks/`。
- 前端纯 UI：`frontend/features/<domain>/components/`，再按子领域建目录。
- 前端纯工具：`frontend/features/<domain>/utils.ts` 或更窄的 `treeUtils.ts`、`presetUtils.ts`。
- 前端 API：`frontend/lib/api/<domain>.ts`，统一从 `client.ts` 走 `apiFetch`、`apiFetchBlob`、`apiSendBinary` 或 `apiFetchEventStream`。
- 后端 HTTP：`backend/app/APIs/routers/<domain>.py`。
- 后端 schema：`backend/app/Schemas/<domain>.py`。
- 后端简单业务：`backend/app/Services/<domain>_service.py`。
- 后端复杂业务：`backend/app/Services/<domain>/service.py` + `repository.py` + 按职责拆分的纯模块。
- 后端基础设施：`backend/app/Utils/`，只能放跨领域通用能力。
- 后端基础设施公共入口 `Utils/db.py`、`Utils/config.py`、`Utils/llm.py` 只保留薄兼容导出；真实实现必须落到同级窄模块。SQLite 连接/迁移分别进入 `db_connection.py`、`db_schema.py`、`db_migrations.py`；配置类型、YAML helper、LLM 配置、生成预设和 settings 聚合分别进入 `config_types.py`、`config_helpers.py`、`config_llm.py`、`config_generation.py`、`config_settings.py`；OpenAI client、请求参数和响应解析分别进入 `llm_client.py`、`llm_options.py`、`llm_parsing.py`。
- 后端测试：`backend/tests/test_<domain>_service.py`，共享 fake 和 builder 放 `tests/fakes.py`、`tests/service_factories.py`。
- 全局打字机版式：后端 schema 放 `backend/app/Schemas/typewriter_layout.py`，Service 和 repository 放 `backend/app/Services/typewriter_layout/`，HTTP 放 `backend/app/APIs/routers/typewriter_layout.py`；前端 API 放 `frontend/lib/api/typewriter-layout.ts`，状态 hook 放 `frontend/features/workspace/hooks/useTypewriterLayoutToolbox.ts`，工具箱 UI 放 `frontend/features/workspace/components/typewriter/`，正文编辑器封装放 `frontend/features/workspace/components/editor/TypewriterTextEditor.tsx`，样式放 `frontend/features/workspace/styles/workspace-typewriter.css`。

## 前端规则

- 前端是展示层，不放权威业务规则。
- 字数、建议、章节排序、项目状态、删除状态、AI 视角解释都以后端返回为准。
- 前端 API client 固定放在 `frontend/lib/api/`；业务代码从 `@/lib/api/index` 或明确领域文件导入，不重建单体 `frontend/lib/api.ts`。
- 前端 API 类型必须按领域放在 `frontend/lib/api/types/`，默认 fallback 与 normalize 必须按领域放在 `frontend/lib/api/fallbacks/`；根部 `types.ts`、`fallbacks.ts` 只允许极薄兼容 re-export，不得新增真实类型、默认数据或业务逻辑。
- 资料区统一使用 Markdown；前端编辑器使用现成开源组件，不手写 Markdown 解析器，预览必须启用 HTML sanitize。
- 建议卡片必须展示后端返回的 `source`，不能把本地降级结果伪装成真实 LLM。
- 页面状态只服务于交互展示，不能成为权威数据源。
- 大型页面必须放在 `frontend/features/<domain>/` 下拆分，`frontend/app/*` 路由入口只做薄封装或 re-export。
- 纯展示组件不直接调用后端 API；后端请求和业务副作用应收敛在页面层或 feature hook。
- Hook 可以管理状态、请求、timer、localStorage 和确认弹窗，但不渲染 JSX；textarea/caret/尺寸测量等 DOM 细节必须留在页面或局部组件层。
- 业务交互禁止使用 `window.alert`、`window.confirm`、`window.prompt`；确认、输入和提示统一通过 `frontend/components/dialog/` 的 `useConfirm()`、`usePrompt()`、`useNotice()`。
- 树结构、预设列表、提示词 draft 转换等可复用无副作用逻辑必须先放进 feature utils，不要散落在 JSX 文件里。
- 组件文件只接收 props 和回调，不读取同级 hook 的内部状态；需要跨组件共享的状态应上提到 feature client 或专门 hook。
- 弹窗、侧栏、树、编辑器、卡片列表等 UI 子领域必须继续放入 `components/<subdomain>/`，避免 `components/` 根目录变成新单体。
- `WorkspaceClient` 和 `LibraryClient` 是页面编排层，不再承接大段新业务。新需求优先扩展 hook、component 或 utils。
- 生成域装配固定归属 `useWorkspaceGenerationController`；`WorkspaceClient` 不直接手工编织 `useGenerationPresets`、`useDraftGeneration`、`useDocumentGeneration` 和 `usePromptPreview` 的共享依赖。
- 正文生成、快速生成、基础铺设、润色和 pending draft 状态机固定归属 `frontend/features/workspace/hooks/draft-generation/`；`hooks/useDraftGeneration.ts` 只保留兼容导出，不得重新堆回业务实现。
- 请求配置状态固定归属 `frontend/features/workspace/hooks/prompts/`；`hooks/usePromptProfiles.ts` 只保留兼容导出。profile draft 构建、保存编排、版本历史读取/恢复和弹窗尺寸状态必须拆分，不得塞回单个 Hook。
- 请求管理弹窗固定由 `components/prompts/PromptManagerDialog.tsx` 组合子面板；请求类型 tabs、素材勾选、最近 N 章、模板占位符插入、输出契约、模型选择、高级配置说明和底部动作必须各自落在窄组件里。
- Dry Run 预览固定由 `components/prompts/PromptPreviewDialog.tsx` 组合子面板；摘要、Context、素材、长文本复制、警告展示必须拆分维护，不能恢复单体预览组件。
- 章节树和资料树的递归渲染、节点行、操作按钮、拖拽投放区和创建/重命名输入固定复用 `frontend/features/workspace/components/tree/`；`ChapterTree.tsx`、`DocumentTree.tsx` 只能保留领域 adapter，不得重新复制整棵树实现。
- `components/tree/TreeView.tsx` 只处理 UI 状态和移动意图，不调用 API、不计算权威排序、不写数据库；章节/资料的保存、删除确认和快照刷新仍归属对应 hook。
- 右侧视角建议栏固定由 `components/perspectives/InsightRail.tsx` 组合子组件；视角列表、视角新增/编辑表单、API 配置选择、队列控制和建议卡片必须拆分维护，不能重新堆回单体右栏。
- 小说工程页的视角 API 配置选择只能引用已有 LLM 配置；新增、编辑、删除 API 配置仍只允许在主页面 API 配置管理中完成。
- `frontend/app/globals.css` 只能作为全局样式入口；tokens、base、响应式和业务样式必须放到 `frontend/styles/` 或对应 `frontend/features/<domain>/` 下。
- 新增跨页面通用 class 前先放入 `frontend/styles/`；只服务单个 feature 的 class 放入该 feature 的 CSS 文件。
- 写作台样式固定由 `frontend/features/workspace/workspace.css` 聚合，真实规则按领域放入 `frontend/features/workspace/styles/`；新增写作台样式必须优先落到 layout、trees、search、editor、documents、actions、perspectives、quick-generation 等窄文件，不能重新堆回聚合入口。
- Feature CSS 禁止长期选择或修饰其他 feature 私有 class；发现跨 feature 样式依赖时，必须把通用 class 提升到 `frontend/styles/`，或把规则迁回拥有该组件的 feature CSS，并同步清理旧选择器。
- 现阶段保留全局 class + 领域 CSS 的过渡方案；不要混入局部 CSS Modules，除非单独规划并由用户完成截图回归。
- 新 UI 控件必须保持简洁、克制、Mac 风格；按钮优先用图标，并提供 `aria-label`。
- 可伸缩侧栏、工具栏、列表行里的“可变文本 / select / input + 固定图标按钮”必须有显式布局契约：固定按钮先包成动作组，文本列使用 `minmax(..., 1fr)` 或等价弹性约束，按钮组使用固定或 `max-content` 宽度；禁止依赖 CSS grid 自动摆放多个按钮，也禁止给主要输入控件写死会阻止宽栏伸展的最大宽度。
- 删除项目、删除视角等破坏性操作必须使用应用内确认弹窗，确认后才调用 API。
- 章节树和资料树的删除按钮必须先显示确认弹窗；目录删除确认必须说明递归影响范围。
- 章节树和资料树拖拽只发送移动意图：`parentId` 与 `beforeNodeId`。前端可以显示插入线和目标目录高亮，但不能本地重算权威树后长期持有；成功后必须使用后端返回的新树，失败后重新加载快照。
- 写作台和主页面的左右栏显示状态与宽度属于本机 UI 偏好，保存到 `localStorage`，不写入项目数据库。
- 打字机版式是全局编辑器视觉偏好，保存到后端 `typewriter_layout_settings` 单行设置，不保存到 `localStorage`，不挂 `project_id`、`chapter_id` 或资料 ID，不跟随作品、章节或导入导出。该设置不得修改正文内容、字数统计、搜索索引、历史版本、AI 上下文或导出结果。段首缩进、段落距离和行距都必须支持 `0.1` 步进，字号必须使用整数步进；段首缩进必须按视觉字符宽度渲染；段落距离必须用 CodeMirror 可测量的行内视觉间距或编辑器 decoration 实现，不得用 `line-height` 冒充，也不得用行外 `margin-bottom` 造成鼠标命中和选区坐标错位；行距只能影响编辑器视觉 line-height，不得影响段落距离字段含义；字号只能影响编辑器视觉 font-size，不得影响正文内容或导出字号。缩进、字号、段落距离或行距变化后，正文编辑器必须触发 CodeMirror 布局重测。
- CodeMirror 正文编辑器的 `readOnly`、`editable` 和其他运行时状态必须优先通过 `Compartment` 或等价可重配置 extension 更新，不得因为 pending、生成中或保存中这类瞬时状态重建整个 `EditorView`。Tab 快速生成、pending draft 聚焦和生成完成自动滚动必须先使用无滚动 selection 更新，再通过 `scrollTextareaIndexIntoView` 这类测量函数按边界余量滚动；禁止在 pending focus 链路里默认调用 `scrollIntoView({ y: "center" })`。修复编辑器滚动类问题时必须分阶段验证，每阶段只改变一个主要变量，临时调试文件或埋点在交付前必须删除，并为 handle 分支补前端单元测试。
- 历史版本管理入口必须放在小说项目内，允许当前章节或资料文本手动保存版本、预览版本和恢复版本。
- Debug 页面入口必须在主页面和小说工程页都可见；Debug 数据写 SQLite，清空操作必须二次确认。
- 写作台不能假定固定项目 ID，必须从路由或 API 返回值读取。

## 后端规则

- 新 endpoint 必须是 `async def`。
- Pydantic 请求、响应和领域数据模型必须放在 `backend/app/Schemas/<domain>.py`；不要恢复旧的集中 `Utils/models.py`。
- 路由和服务应从明确的 `app.Schemas.<domain>` 导入 schema，避免重新形成单体模型入口。
- `Schemas/__init__.py` 只能作为包聚合出口，不允许把新 schema 都塞进这里。
- Router 只能做 HTTP 层：参数绑定、response model、状态码和调用 Service；不能写 SQL、不能直接读写文件、不能拼 LLM 请求。
- Service 负责业务编排；SQL row mapping 进入 repository，默认模板/契约/渲染/素材展开等纯职责进入独立模块。
- 系统启动不得自动创建默认小说或演示项目；空库必须保持为空，只有显式 `POST /api/projects` 才能创建小说。
- 单文件 Service 超过纪律线时，优先拆 repository；已有 repository 后再按纯职责拆 helper 模块。
- SQLite 访问必须通过 `Utils/db.py` 导出的 `AsyncDatabase`；业务层不得直接使用 `aiosqlite`。
- 文件 I/O 必须经过 `AsyncFileStore`。
- 写项目数据必须考虑项目级或章节级锁。
- 全局打字机版式 API 固定为 `/api/typewriter-layout-settings`，不得塞进项目路由或章节路由；Service 只允许读写 `typewriter_layout_settings` 单行设置，不得读取或写入项目正文。
- 项目生命周期实现固定放在 `Services/projects/`；旧 `project_service.py` 只能保留薄 re-export。SQL 和 row mapping 进入 `repository.py`，创建/旧项目导入/默认文件写入进入 `lifecycle.py`，软删除和恢复进入 `trash.py`。
- 章节目录树元数据必须保存到 SQLite 的 `chapter_nodes`；目录没有文件，章节节点通过 `chapter_id` 指向 `chapters`。
- 章节节点移动必须在章节锁内校验目标目录、插入位置和子孙关系；移动后必须重算同级 `chapter_nodes.order_index`，并按树前序重建全局 `chapters.order_index`。
- 章节正文保存时必须同步更新 `chapters.word_count`、章节节点更新时间、项目更新时间和 `chapter_search_fts` 搜索索引。
- 章节搜索禁止每次请求扫描 `chapters/*.md` 文件；必须使用 SQLite FTS5 索引，短词 fallback 也只能查索引内容表。
- 章节服务实现必须保持在 `Services/chapters/` 包内分层：`service.py` 只做业务编排，SQL 和 row mapping 进入 `repository.py`，树移动进入 `tree.py`，正文 I/O 进入 `content.py`，FTS 进入 `search_index.py`，删除进入 `deletion.py`。旧 `chapter_service.py` 只能保留薄 re-export。
- 全项目搜索固定归属 `Services/search/`、`Schemas/search.py`、`APIs/routers/search.py`、`frontend/lib/api/search.ts` 和 `features/workspace/components/search/`；不得把搜索查询、snippet、高亮或跨资源合并逻辑塞回章节/资料组件。
- 全项目搜索后端必须保持 `Services/search/` 分层：`service.py` 只做薄编排，SQL/FTS 查询进入 `repository.py`，query 解析和 scope 映射进入 `query.py`，排序规则进入 `ranking.py`，snippet 进入 `snippets.py`，资源构建和结果 metadata 转换进入 `resources.py`。
- 任何新增的可搜索资源都必须接入 `project_search_meta` / `project_search_fts`，并提供稳定的 `resource_type`、`resource_id`、`path_text`、`content_hash` 和跳转 metadata。
- 搜索请求必须先走后端统一索引；禁止前端为了搜索而遍历章节、资料、提示词或版本全文。短词 fallback 也只能查索引内容表。
- Embedding 能力必须作为通用模型基础设施维护，固定归属 `Services/embeddings/`、`Schemas/embeddings.py`、`APIs/routers/embeddings.py` 和 `frontend/lib/api/embeddings.ts`。热图、语言簇、语义搜索、主题曲线等都只能复用同一套 runtime、模型签名和 Chroma 缓存层，不得各自直接调用供应商或自建向量缓存。
- Embedding 后端必须保持 `Services/embeddings/` 分层：`service.py` 只做门面编排，分析流程进入 `analysis_service.py`，SQLite row 组装进入 `analysis_rows.py`，SQL 和 row mapping 进入 `repository.py`，OpenAI-compatible embeddings 调用进入 `model_runtime.py`，Chroma 读写进入 `chroma_store.py`，模型签名和 cache key 进入 `cache.py`，缓存命中 / 缺失合并进入 `cache_runtime.py`，切片进入 `segmentation.py`，热图距离和归一化进入 `heatmap.py`，聚类分配进入 `clustering.py`，投影进入 `projection.py`。
- Embedding 前端固定归属 `frontend/lib/api/embeddings.ts`、`frontend/lib/api/types/embeddings.ts`、`frontend/features/workspace/hooks/useEmbeddingToolbox.ts`、`frontend/features/workspace/components/embeddings/` 和 `frontend/features/workspace/styles/workspace-embeddings.css`。`WorkspaceClient` 只装配 hook，layout/topbar 只传 props 和触发开关；抽屉、标签管理、设置、热图控制、语言簇控制、图谱和 overlay 不得塞回写作台大文件。
- 所有正式 Embedding 请求必须使用已有 `kind=embedding` API 配置，并进入 `ModelRequestQueueService`；禁止业务 Service 绕过模型队列直接调用 OpenAI SDK。队列快照和普通 API 摘要不得返回正文全文、向量、API Key、Authorization header 或供应商敏感字段。
- Chroma 只作为 `backend/data/chroma/` 下的本地向量缓存，不作为项目权威业务数据库。项目标签、分析 run、offset、热图分数、聚类坐标和错误摘要必须写 SQLite；模型签名必须隔离 API 配置 ID、provider、base URL、model 和 dimensions。
- 章节或资料热图 overlay 不得修改正文，不得影响自动保存、历史版本、字数统计和搜索索引。切片 offset 必须按完整正文坐标返回，前端只能展示后端结果。
- 删除章节节点必须递归清理 `chapter_nodes`、`chapters` 和 `chapter_search_fts`，正文文件只能移动到 trash，并写入 manifest；不能直接物理删除。
- 资料文档、大纲、设定等项目文件必须通过 `DocumentService` 暴露，不允许路由直接拼路径读取。
- 资料目录树元数据必须保存到 SQLite 的 `document_nodes`；目录没有文件，Markdown 节点正文保存到项目 `docs/` 下的 `.md` 文件。
- `/documents` 摘要接口只能从 `document_nodes` 中的 `outline` / `design` / `note` Markdown 节点派生，不允许重新引入独立 `documents` 表或双写分支。
- 资料节点移动必须在资料锁内校验目标目录、插入位置和子孙关系；移动后只更新 `document_nodes.parent_id/order_index`，不得因为目录移动重命名 Markdown 文件路径。
- 章节和资料正文保存的 `base_updated_at` 是后端 `updated_at` 不透明字符串；前端必须原样回传最近一次 GET / 保存响应中的值，后端比对处保持字符串 token 比对。
- 资料正文必须自动保存，保存时同时更新资料节点和项目更新时间。
- 删除资料节点必须递归清理 `document_nodes`，Markdown 文件只能移动到 trash，并写入 manifest；不能直接物理删除。
- 资料服务实现必须保持在 `Services/documents/` 包内分层：`service.py` 只做业务编排，SQL 和 row mapping 进入 `repository.py`，树处理进入 `tree.py`，Markdown I/O 进入 `content.py`，删除进入 `deletion.py`。旧 `document_service.py` 只能保留薄 re-export。
- 历史版本元数据必须写入 SQLite 的 `resource_versions`；正文快照必须写入项目 `versions/` 目录，不把长文本正文塞进 SQLite。
- 自动保存不能逐次写入历史版本；必须通过 `version_settings` 的时间间隔、变化字数和变化比例节流。
- 恢复历史版本前必须先写入 `pre_restore` 版本，再覆盖当前章节或资料正文。
- LLM 调用只能放在 Service 或 Utils client 中，路由不能直接请求模型服务。
- LLM 供应商调用必须走 OpenAI Python SDK 和 OpenAI Chat Completions 标准；不要新增手写 HTTP 请求路径。
- LLM 请求参数默认放在 `backend/config/llm.yaml`，后端启动时读取一次；修改 YAML 后必须重启后端。
- API 配置必须作为全局固定配置保存到 SQLite 的 `api_configs`，只允许在主页面子菜单里新建、保存、更新和删除，不允许在小说工程页编辑。
- API 配置相关实现固定放在 `Services/api_configs/`；模板、runtime、健康检查、repository 和业务编排分文件维护，不再新增旧式平铺服务入口。
- API 配置必须区分 `max_tokens` 与 `context_window_tokens`：前者是发送给供应商的输出 token 预算，后者是本地上下文窗口检查上限，不得把二者混用。
- 小说库前端必须保持薄入口：`LibraryClient` 只负责页面组合、选中状态和 hook 装配；项目列表放在 `features/library/components/projects/`，API 配置列表和表单放在 `features/library/components/api-configs/`。API 配置表单必须按供应商入口、模型、密钥、请求参数分段，不再把所有字段堆回单个组件。`features/library/library.css` 只作为聚合入口，新增小说库样式应进入 `features/library/styles/` 的对应领域文件。
- 新建 API 配置必须先选择 API 类型和供应商模板；内置模板至少覆盖 DeepSeek、OpenAI、Gemini、Grok、SiliconFlow、Ollama、LM Studio 和 vLLM，并同时规划 LLM 与 Embedding。
- `api_configs.kind` 必须区分 `llm` 和 `embedding`；默认配置和最后一套配置按 kind 隔离保护。API 配置创建后不得修改 `kind`，需要换类型必须新建配置；Embedding 配置不能被写作视角或 Prompt Profile 的 LLM 请求配置引用，只能由 Embedding 工具箱等语义分析能力选择。
- API 配置健康检查必须复用真实运行参数，LLM 检查验证非流式 JSON object，Embedding 检查验证向量维度；健康检查不写业务 Debug Log，不累计 Token usage。
- 小说工程里的每个视角只能保存 LLM `api_config_id` 引用；同一本小说里的不同视角可以选择不同 LLM API 配置，互不干扰。视角建议请求优先使用视角自己的 `api_config_id`，否则回退到请求配置里的 `config.api_config_id`，再回退默认 LLM 配置。视角建议请求必须按视角独立调用、独立校验、独立降级，即使多个视角使用同一配置也不能合并请求。
- 请求管理里的每类请求配置都可以在 `config.api_config_id` 选择一套 LLM API 配置，也可以在 `config.temperature` 保存请求级 Temperature；保存时必须校验 API 配置 ID 存在且为 `kind=llm`，空白值必须清理，Temperature 必须规范化为 0 到 2 之间的数字或清理为空。删除全局 API 配置时必须清理 Prompt Profile 中对该配置的请求级引用，保留其它 config 字段，让请求回退到默认 LLM。正文续写、Tab 快速生成、正文润色、章节基础铺设、资料润色、资料续写、视角建议、作品聊天、Prompt Preview 和 Dry Run 都必须按请求类型读取该配置；`config.temperature` 存在时优先于最终 API 配置里的 Temperature。
- Tab 快速生成在右侧栏拥有最贴近用户的设置入口，模型、Temperature、用户可编辑 System 提示词和 User 提示词必须直接读写 `quick_generate_next_paragraph` Prompt Profile 的 SQL 内容，执笔作者人格完整菜单也固定放在右侧栏并复用 `author_persona` 预设。System/User 提示词中的 `{input.*}` 占位符必须原样保存并由后端统一 renderer 渲染；即使用户改写 System 提示词，后端也必须继续追加结构化 JSON 输出契约。右侧栏不得再为 Tab 快速生成维护独立的 Temperature、System、User 模板或作者人格覆盖层；悬浮球不再提供快速设置入口，快速生成也不得再把旧 `quick_generation_mode` 任务提示词注入最终 prompt。
- 所有真实外部模型供应商请求必须进入 `ModelRequestQueueService`，包括视角建议、正文续写、Tab 快速生成、正文润色、章节基础铺设、资料润色、资料续写、作品聊天、Embedding 热图 / 语言簇分析、LLM 健康检查和 Embedding 健康检查；禁止业务 Service 或健康检查直接绕过模型队列调用 OpenAI SDK。
- 所有业务 LLM 请求进入模型队列前必须用最终 messages 检查 `input_tokens + max_tokens <= context_window_tokens`。超出时必须返回明确上下文超出错误，不得调用供应商，不得静默降级成本地生成。
- 模型队列快照接口只能返回请求类型、状态、优先级、模型和时间戳等元信息；不得返回 prompt、正文、响应体、API Key、Authorization header 或其他敏感数据。
- `/suggestions` HTTP 入口必须先进入 `SuggestionQueueService`。视角队列可以去重、排序和替换旧自动任务，但不能直接拼 prompt，不能直接调用 LLM，也不能把多个视角合成一个模型请求；真实供应商调用仍必须进入 `ModelRequestQueueService`。
- 视角建议触发来源必须显式标记为 `manual`、`batch` 或 `auto`。`manual` 优先级最高，`auto` 优先级最低；同一章节同一视角的新自动请求可以替换尚未开始执行的旧自动请求。
- 视角建议默认手动触发；工作台快照和章节保存不得默认等待建议请求。自动建议只能由前端显式开关启用，且必须在正文保存完成后以后台单视角请求发起，不能阻塞保存、打开项目或其他视角。
- LLM API 配置里的 `temperature`、`top_p`、`top_k` 都是可选采样参数；空值表示不覆盖、不发送。`top_k` 不是 OpenAI Chat Completions 标准白名单字段，必须通过 `extra_body` 传给兼容供应商。
- 结构化写作类 LLM 请求必须是非流式 JSON 请求：`stream=false` 且 `response_format.type=json_object`。覆盖视角建议、正文续写、Tab 快速生成、正文润色、章节基础铺设、资料润色、资料续写和 LLM 健康检查。
- 作品聊天是明确例外：`chat_about_work` 允许 `stream=true` 和非 JSON 自由文本，必须移除 `response_format`，允许 Markdown。它仍必须走 OpenAI SDK、`ModelRequestQueueService`、项目级 PromptProfile、Debug Log 和 Token usage 统计。
- 聊天会话接口属于项目级资源，必须先校验 `project_id` 存在，再读取、新建、重命名、删除会话或持久化消息；SSE `[DONE]` 只能在会话消息保存成功后发送，不能吞掉持久化异常伪装成成功。
- DeepSeek、SiliconFlow 等供应商扩展字段必须通过 SDK 的 `extra_body` 发送；运行时 `base_url`、模型和请求参数来自视角选择的 API 配置。DeepSeek 关闭思考时也必须显式发送 `extra_body.thinking.type=disabled`；开启时发送 `extra_body.thinking.type=enabled`，并用顶层 `reasoning_effort=high|max` 区分普通/努力思考。
- 每类结构化 LLM 请求都必须有后端强制输出契约；契约必须包含 `json` 字样和 JSON 示例，不能只依赖用户可编辑提示词。作品聊天使用非 JSON 对话输出约定，不得套用结构化 JSON 契约。
- 每类结构化 LLM 请求都必须在 `Services/structured_outputs/` 注册强制 schema。新增结构化请求时必须同步修改 `schemas.py`、`validators.py`、`contracts.py` 和测试；不能只写提示词契约。新增自由文本请求必须在文档中写明非结构化边界、Debug 记录方式和是否流式。
- LLM schema 校验必须发生在 `structured_llm_service.complete_json()` 内、Debug success 写入前。校验失败必须记录 Debug error 和 schema error，不得把 `{}`、空 `text`、非法枚举或未知视角 ID 当成可用结果。
- 请求配置里的章节素材选择必须同时保留固定章节和最近 N 章两种模式；最近 N 章只在请求时按当前章节动态展开，并与固定章节按顺序去重。
- 所有业务 LLM 请求必须先构造 `PromptContextPack`，再渲染为最终 System/User。新请求不得绕过 `PromptContextBuilder` 手写平铺上下文；资料原文必须放入 fenced block，不能让资料 Markdown 标题污染外层 prompt 层级。作品聊天也必须通过 `PromptProfileService.build_preview()` 生成最终上下文，再把对话历史追加到消息列表。
- 每类 LLM 请求都必须支持 Dry Run 预览；预览必须复用正式提示词拼装逻辑，不能在前端重新拼一套近似提示词。
- LLM Debug 的原始 request body 必须保持供应商实际请求体；`context_pack` 只能存放在独立 Debug 字段和 `debug_readable` 中。Debug 页面展示的 System/User 必须来自最终渲染后实际发送给模型的 `messages`，不能展示未渲染模板或中间对象替代品。
- Embedding Debug 必须使用 `model_kind=embedding` 的通用模型请求日志，只保存脱敏摘要，不保存完整 `input` 文本数组、正文切片、资料片段、标签描述或 `data[].embedding` 向量。允许保存 model、dimensions、input_count、短 hash、cache stats、tool/resource/run、embedding_count、embedding_dimensions、usage、duration 和错误类型。
- Debug 页面必须保持薄入口：`DebugClient` 只做页面组合，范围切换放在 `useDebugScope`，请求快照、展开项和清空动作放在 `useDebugLogs`，Token 统计、Log 列表、详情 Tabs、可读化面板和 JSON/Text 展示放在 `features/debug/components/`。进入“全部”范围时必须保留 `return_project_id`，保证能稳定切回来源项目；清空统计、清空 Log 和清空全部必须保留二次确认。
- 请求配置每次显式保存都必须写入 `prompt_profile_versions`；首次保存前保留 `initial` 快照，恢复历史前保留 `pre_restore` 快照，恢复动作不能反写 YAML 默认配置。
- 请求配置相关实现固定放在 `Services/prompt_profiles/`；默认模板、强制输出契约、素材展开、渲染、版本历史和 repository 必须保持分层。
- 续写正文、Tab 快速生成、章节基础铺设和资料生成预设默认放在 `backend/config/generation.yaml`；项目内修改、删除、新增只写 SQLite 的 `generation_presets`，读取时必须先应用数据库覆盖/隐藏，再 fallback 到 YAML 默认。
- 生成服务实现固定放在 `Services/generation/`；旧 `generation_service.py` 只能保留薄 re-export。预设读写/YAML fallback 进入 `preset_resolution.py`，runtime input 进入 `request_inputs.py`，结构化 LLM 调用进入 `runtime.py`，正文、润色、资料和章节铺设分别进入对应 action 模块，不得把新请求继续塞回单体 Service。
- Dry Run 后端实现固定放在 `Services/prompt_preview/`；旧 `prompt_preview_service.py` 只能保留薄 re-export。预览输入、API 配置/请求参数、token 估算和 preview item 构建必须分文件维护，且必须复用 `PromptProfileService.build_preview()`。
- 续写、润色等正文类 LLM 响应也必须是 JSON object，并从 `text` 字段提取最终正文；不能把模型原文直接当正文。作品聊天的模型原文可以直接作为聊天气泡展示，但不能被当成正文或资料内容自动写回。
- 资料润色/续写也必须走请求管理页、项目级预设和强制 JSON 链路；返回的 `text` 是 Markdown 片段，前端采纳时才替换选区或追加到资料末尾。
- LLM 密钥可以在全局 API 配置里保存到本地 SQLite；不能提交到仓库，GET 接口也不能返回明文 key。
- 结构化 LLM 输出必须按 JSON 解析和 schema 校验，不能把模型原文直接透传给前端；正文/资料生成只接受顶层 `text` 非空字符串，章节基础铺设只接受顶层 `points` 非空字符串数组，视角建议只接受合法 `cards` 数组和当前输入视角 ID。作品聊天不做 JSON 解析和 schema 校验，但 Debug readable 不得把非 JSON 聊天内容标为 schema error。
- LLM 不可用时必须有明确降级策略，并在响应里标记 `source=local`。
- 模型 Debug 日志必须从统一请求出口写入，并用 `model_request_logs` / `model_token_usage_daily` 按 `model_kind` 区分 LLM 与 Embedding。LLM 保留原始 request body / response body；Embedding 只保留脱敏供应商请求摘要。两类日志都不得保存 API Key、Authorization header 或其他密钥；Debug API 的可读视图必须由后端统一派生并二次脱敏，前端只负责展示对应模型类型的摘要、参数、请求和返回。流式聊天必须记录实际 `stream=true` 请求体和原始 stream chunks，不能用非流式 JSON 快照冒充原始请求。
- Token 统计只能使用供应商返回的 `usage`；本地估算值不得混入真实 Token 统计。
- Prompt Preview 的 `token_estimate` 只能作为请求规划用的粗略上下文长度提示；它不得写入 Debug usage、不得进入每日 Token 统计，也不得被业务逻辑当成真实供应商计费数据。
- 项目导出 / 导入固定归属 `Services/project_transfer/`、`Schemas/project_transfer.py`、`APIs/routers/project_transfer.py` 和 `frontend/lib/api/project-transfer.ts`；不得把 zip 处理、manifest 校验或导入 SQL 堆回 `ProjectService`。
- 项目导入器必须保持分层：`importer.py` 只做流程编排；导入数据校验和必需文件检查进入 `import_validation.py`，内容文件落盘进入 `import_files.py`，SQLite 写入、API 配置映射和搜索索引重建进入 `import_database.py`，失败清理进入 `import_cleanup.py`。导入必须永远创建新项目，遇到同 ID 或同目录时生成新 ID，不覆盖现有项目。
- 项目导出默认必须排除 API Key 明文；导入永远创建新项目，不能覆盖现有项目；任何 zip 内路径都必须经过 Zip Slip 检查和 checksum 校验。
- 前端项目导入必须捕获失败并给出用户可见提示；导入失败不能刷新列表或改变当前选中项目，文件 input 必须清空以允许同一文件重试。
- 正文 `.docx` 导出属于章节阅读输出，固定走 `ChapterDocxExportService`、`ExportChaptersDocxRequest` 和 `frontend/lib/api/chapters.ts`；不得复用项目 zip 导出，也不得在 `.docx` 中夹带资料、提示词、Debug 日志或项目备份 manifest。
- 导入写入必须有事务边界和失败清理：SQLite 回滚后，本次新建项目目录也要清理或移入 trash，不能留下半项目。
- 项目删除必须是软删除：数据库写 `deleted_at`，目录移动到 trash，不直接物理删除。
- 新错误类型必须在 `APIs/error_handlers.py` 中映射。
- CORS 来源不能散落在路由里。
- 任何路径拼接必须经过 `PathResolver` 或项目目录下的固定子路径。

## SQLite 规则

- 启动时必须执行幂等迁移。
- 必须启用 `PRAGMA foreign_keys = ON`。
- 必须启用 WAL，以降低读写互相阻塞。
- 迁移默认只允许向前追加，不允许在运行时破坏用户数据；若当前数据被明确标记为测试数据且用户授权丢弃旧数据，破坏性收敛必须同步更新 schema、导入导出格式、测试和基础文档。
- 旧 `manifest.json` 可以作为导入来源，但导入后 SQLite 是权威元数据。
- 除非有用户授权，不可进行“生产危险”操作。

## 测试规则

- 修改 `Utils` 时至少补单元测试。
- 修改 `Schemas` 时至少跑相关 router/service 测试；字段或 validator 变化必须补断言。
- 修改 `Services` 时补服务测试或 API 集成测试；复杂 Service 包内 repository/runtime/materials 等模块应优先补窄单元测试。
- 后端服务测试必须按领域放入 `backend/tests/test_<domain>_service.py`；不要重新堆回单体 `test_services.py`。
- 生成服务测试必须继续按能力拆分为 presets、draft、polish、document、blueprint 等窄文件；不要恢复 `backend/tests/test_generation_service.py`。
- 共享 fake LLM、fake health checker 和 service builder 必须放在 `tests/fakes.py` 或 `tests/service_factories.py`，不要在单个测试文件里重复实现。
- 前端改 hook、API client、组件或配置必须跑 `npm run lint --prefix frontend` 和 `npm run typecheck --prefix frontend`；改可视组件或 CSS 时，Codex 必须在交付说明中列出建议验证点，由用户完成浏览器烟测。
- 修改可伸缩侧栏、响应式布局或行内动作区时，建议用户浏览器烟测覆盖最小宽度、默认宽度和最大宽度；至少确认按钮不越出父容器、可变控件会随容器伸缩、文字溢出按设计省略或换行。
- Next 16 不再使用 `next lint`。本项目的前端 lint 固定走 ESLint 9 flat config：`frontend/eslint.config.mjs`，脚本为 `npm run lint --prefix frontend`。该脚本通过 `frontend/scripts/lint-with-timeout.mjs` 分段运行 ESLint，并用 `ESLINT_CHUNK_TIMEOUT_MS` 为每段设置 watchdog，避免偶发卡死时无限等待。不要恢复 `.eslintrc.json`、`next lint` 或无 watchdog 的全量裸 ESLint 命令。
- 生产前端构建必须保留 `frontend/scripts/clean-next-build.mjs` 和 `frontend/scripts/verify-next-build.mjs` 链路；不要把 `npm run build --prefix frontend` 改回裸 `next build`。直接运行裸构建可能留下全局路由表存在、实际 App route entry 或 client reference manifest 缺失的半坏 `.next`。
- 修改 `frontend/lib/api/` 必须确认领域文件没有直接绕过 `client.ts` 的请求逻辑；浏览器 `fetch` 只能出现在 `client.ts` 的统一出口中。
- 修改 API 响应结构时同步更新 `docs/backend-api.md`。
- 修改目录、层级、数据流时同步更新 `docs/architecture.md`。
- 修改提示词、LLM 配置或模型响应结构时同步更新架构文档和 API 文档。
- 修改破坏性操作时必须覆盖确认前端逻辑或后端软删除服务测试。

## 文件大小纪律

不是编译规则，但超过后必须拆分，不能把“能跑”当作继续堆代码的理由。

- React 页面入口：不超过 400 行。
- React 组件文件：不超过 250 行。
- Hook 文件：不超过 250 行。
- 领域 CSS 文件：不超过 500 行。
- 后端 Service：不超过 450 行。
- Repository：不超过 350 行。
- Schema 文件：不超过 300 行。
- 单个测试文件：不超过 500 行。

当前仍偏大的文件必须视为后续重构优先对象：接近纪律线的 context builder、前端 Hook 和测试文件等后续新增需求不得继续直接堆入，应先拆窄模块。

当前允许保留但不能继续增长的历史基线：

- `frontend/features/workspace/hooks/useGenerationPresets.ts`：284 行。后续修改该领域时，优先拆分预设读取、草稿编辑、保存/删除动作。
- `frontend/features/workspace/hooks/useChapterTreeActions.ts`：280 行。后续修改该领域时，优先拆分创建/重命名、移动、删除确认、刷新快照。
- `backend/app/Services/prompt_profiles/context_builder.py`：约 445 行，虽未超出 450 行纪律线，但继续新增 PromptContext 逻辑前必须先拆分章节素材、资料素材、focus 构建和预算统计。

模块体量检查固定使用：

```bash
./scripts/check-module-size.py
```

该脚本会检查前端页面入口、组件、Hook、领域 CSS、前端支撑模块、后端 Service、Repository、Schema、后端支撑模块和测试文件。当前历史超线文件记录在脚本的 `BASELINE_DEBT` 中：这些文件可以作为重构债务继续存在，但不能超过记录的基线行数；新增文件或已拆分文件超线会直接失败。后续每完成一个重构阶段，都应运行该脚本，并在目标文件回到纪律线后从 `BASELINE_DEBT` 移除对应项。

## 提交前检查

通用：

```bash
git diff --check
./scripts/check-module-size.py
```

后端：

```bash
conda run -n novel pytest -q
```

前端：

```bash
npm run lint --prefix frontend
npm run typecheck --prefix frontend
npm run build --prefix frontend
```

`npm run lint --prefix frontend` 正常输出应按 `app`、`features/library`、`features/workspace`、`features/debug + model queue`、`lib`、`scripts + eslint config` 分段通过；如果某段超时，命令会返回 `124` 并打印卡住的分段。交付前不能把超时当作通过，必须继续定位对应分段，或在交付说明中写清无法完成验证的具体分段和原因。

如果因为依赖未安装、网络或本地环境无法运行，必须在交付说明中写清楚。

## 提交信息规范

为了让 `git log` 可读、可回退、可 bisect，提交必须原子且信息准确。

- **格式**：`<type>(<scope>): <subject>`，subject 用祈使句、中文或英文均可、不超过约 50 字。
  - type：`feat`（新能力）、`fix`（修 bug）、`refactor`（不改行为）、`docs`（仅文档）、`test`（仅测试）、`chore`（构建/脚本/依赖）、`style`（仅格式）。
  - scope 可选，标注领域，如 `backend`、`frontend`、`chapters`、`chat`、`css`。
- **原子性**：一个提交只做一件事；不把多个阶段/多个领域混在一个提交里。涉及多文件但同一逻辑改动可以合在一起。
- **信息必须描述真实变更**，不能只用元描述（如"add plan"）当成代码提交的标题；若一个提交含多项，subject 概括、body 用列表逐项说明。
- **不提交临时工作文档**（issue 报告、施工计划等）；确需留痕就单独一个 `docs:` 提交，且不要"加了又删"制造历史噪音。
- **破坏性操作单独成提交或显式说明**：改写历史的 `reset`/`rebase` + `force-push` 属高危，必须先确认目标，用 `--force-with-lease`。
- **Co-Authored-By**：由 Claude 协作的提交，消息末尾加 `Co-Authored-By: Claude <noreply@anthropic.com>`。
