"use client";

import { Search, X } from "lucide-react";
import type {
  ProjectSearchResourceType,
  ProjectSearchResult,
  ProjectSearchScope,
} from "@/lib/api/index";
import type { ProjectSearchGroup } from "@/features/workspace/hooks/useProjectSearch";

const scopeOptions: { value: ProjectSearchScope; label: string }[] = [
  { value: "all", label: "全部" },
  { value: "chapters", label: "章节" },
  { value: "documents", label: "资料" },
  { value: "prompts", label: "请求" },
  { value: "presets", label: "预设" },
  { value: "versions", label: "版本" },
];

const typeLabels: Record<ProjectSearchResourceType, string> = {
  chapter: "章节",
  document: "资料",
  prompt_profile: "请求配置",
  prompt_profile_version: "请求历史",
  generation_preset: "预设",
  resource_version: "版本",
};

export function ProjectSearchPanel({
  groups,
  isLoading,
  onOpenResult,
  query,
  scope,
  setQuery,
  setScope,
}: {
  groups: ProjectSearchGroup[];
  isLoading: boolean;
  onOpenResult: (result: ProjectSearchResult) => void;
  query: string;
  scope: ProjectSearchScope;
  setQuery: (query: string) => void;
  setScope: (scope: ProjectSearchScope) => void;
}) {
  const isActive = Boolean(query.trim());
  return (
    <section className="project-search-panel" aria-label="全项目搜索">
      <label className="rail-search project-search-box">
        <Search size={14} />
        <input
          aria-label="搜索全项目"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="搜索章节、资料、请求配置、版本"
          value={query}
        />
        {query ? (
          <button
            className="tiny-tool"
            onClick={() => setQuery("")}
            type="button"
            aria-label="清空全项目搜索"
          >
            <X size={13} />
          </button>
        ) : null}
      </label>
      <div className="project-search-scopes" aria-label="搜索范围">
        {scopeOptions.map((option) => (
          <button
            aria-pressed={scope === option.value}
            className={scope === option.value ? "scope-chip active" : "scope-chip"}
            key={option.value}
            onClick={() => setScope(option.value)}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>
      {isActive ? (
        <div className="project-search-results" aria-label="全项目搜索结果">
          {isLoading ? <p className="empty-note">正在搜索...</p> : null}
          {!isLoading && !groups.length ? (
            <p className="empty-note">没有找到“{query.trim()}”</p>
          ) : null}
          {!isLoading
            ? groups.map((group) => (
                <div className="project-search-group" key={group.key}>
                  <div className="project-search-group-title">
                    <span>{group.label}</span>
                    <small>{group.results.length}</small>
                  </div>
                  {group.results.map((result) => (
                    <button
                      className="project-search-result"
                      key={`${result.resource_type}:${result.resource_id}`}
                      onClick={() => onOpenResult(result)}
                      type="button"
                    >
                      <span className="result-type">{typeLabels[result.resource_type]}</span>
                      <strong>{result.title}</strong>
                      {result.path.length ? <small>{result.path.join(" / ")}</small> : null}
                      {result.matches[0] ? (
                        <MarkedSnippet snippet={result.matches[0].snippet} />
                      ) : null}
                    </button>
                  ))}
                </div>
              ))
            : null}
        </div>
      ) : null}
    </section>
  );
}

function MarkedSnippet({ snippet }: { snippet: string }) {
  const parts = snippet.split(/(<mark>|<\/mark>)/);
  let marked = false;
  return (
    <p className="search-snippet">
      {parts.map((part, index) => {
        if (part === "<mark>") {
          marked = true;
          return null;
        }
        if (part === "</mark>") {
          marked = false;
          return null;
        }
        return marked ? <mark key={index}>{part}</mark> : <span key={index}>{part}</span>;
      })}
    </p>
  );
}
