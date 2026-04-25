import {
  BookMarked,
  CircleDot,
  FilePlus2,
  Keyboard,
  KeyRound,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import type { LibrarySnapshot, ProjectStatus } from "@/lib/api/index";
import type { LibraryPanel } from "@/features/library/types";
import { statusLabels } from "@/features/library/utils";

export function LibrarySidebar({
  activePanel,
  library,
  onOpenApiConfigCreate,
  onOpenProjectCreate,
  query,
  setActivePanel,
  setQuery,
  setStatusFilter,
  statusFilter,
}: {
  activePanel: LibraryPanel;
  library: LibrarySnapshot;
  onOpenApiConfigCreate: () => void;
  onOpenProjectCreate: () => void;
  query: string;
  setActivePanel: (panel: LibraryPanel) => void;
  setQuery: (query: string) => void;
  setStatusFilter: (status: ProjectStatus | "all") => void;
  statusFilter: ProjectStatus | "all";
}) {
  return (
    <aside className="library-sidebar" aria-label="小说库筛选">
      <div className="brand-row">
        <div className="brand-mark">D</div>
        <div>
          <p className="eyebrow">Deep Novel Typer</p>
          <h1>小说库</h1>
        </div>
      </div>

      <div className="library-stats">
        <div>
          <strong>{library.stats.active_count}</strong>
          <span>项目</span>
        </div>
        <div>
          <strong>{library.stats.total_words}</strong>
          <span>总字数</span>
        </div>
      </div>

      <div className="library-menu" aria-label="主页面子菜单">
        <button
          className={activePanel === "projects" ? "nav-pill active" : "nav-pill"}
          onClick={() => setActivePanel("projects")}
          type="button"
        >
          <BookMarked size={14} />
          小说项目
        </button>
        <button
          className={activePanel === "api-configs" ? "nav-pill active" : "nav-pill"}
          onClick={() => setActivePanel("api-configs")}
          type="button"
        >
          <KeyRound size={14} />
          API 配置
        </button>
        <button
          className={activePanel === "save-settings" ? "nav-pill active" : "nav-pill"}
          onClick={() => setActivePanel("save-settings")}
          type="button"
        >
          <SlidersHorizontal size={14} />
          保存机制
        </button>
        <button
          className={activePanel === "shortcut-settings" ? "nav-pill active" : "nav-pill"}
          onClick={() => setActivePanel("shortcut-settings")}
          type="button"
        >
          <Keyboard size={14} />
          快捷键
        </button>
      </div>

      {activePanel === "projects" ? (
        <>
          <div className="api-action-stack project-action-stack" aria-label="小说项目操作">
            <button className="side-action-button" onClick={onOpenProjectCreate} type="button">
              <FilePlus2 size={14} />
              新建小说
            </button>
          </div>

          <label className="search-box">
            <Search size={16} />
            <input
              aria-label="搜索小说"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索书名、类型、简介"
              value={query}
            />
          </label>

          <div className="filter-stack" aria-label="状态筛选">
            {(["all", "planning", "drafting", "revising", "completed"] as const).map(
              (status) => (
                <button
                  className={statusFilter === status ? "filter-pill active" : "filter-pill"}
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  type="button"
                >
                  <CircleDot size={14} />
                  {status === "all" ? "全部" : statusLabels[status]}
                </button>
              ),
            )}
          </div>
        </>
      ) : activePanel === "api-configs" ? (
        <div className="api-action-stack" aria-label="API 配置操作">
          <button
            className="side-action-button"
            onClick={onOpenApiConfigCreate}
            type="button"
          >
            <FilePlus2 size={14} />
            新建配置
          </button>
        </div>
      ) : activePanel === "save-settings" ? (
        <div className="api-action-stack" aria-label="保存机制说明">
          <p className="empty-note">
            自动保存仍然实时保护当前稿；历史版本只在有意义的变化点生成。
          </p>
        </div>
      ) : (
        <div className="api-action-stack" aria-label="快捷键说明">
          <p className="empty-note">
            快捷键设置保存在本机浏览器，只影响当前设备的写作台交互。
          </p>
        </div>
      )}
    </aside>
  );
}
