"use client";

import { useEffect, useMemo, useState } from "react";
import {
  searchProject,
  type ProjectSearchResourceType,
  type ProjectSearchResult,
  type ProjectSearchScope,
} from "@/lib/api/index";
import type { ProjectSearchApi, ProjectSearchGroup } from "./workspaceInteractionApiTypes";

export type { ProjectSearchApi, ProjectSearchGroup } from "./workspaceInteractionApiTypes";

const groupLabels: Record<ProjectSearchResourceType, string> = {
  chapter: "章节",
  document: "资料",
  prompt_profile: "请求配置",
  prompt_profile_version: "请求历史",
  generation_preset: "生成预设",
  resource_version: "正文/资料版本",
};

const groupOrder: ProjectSearchResourceType[] = [
  "chapter",
  "document",
  "prompt_profile",
  "generation_preset",
  "prompt_profile_version",
  "resource_version",
];

export function useProjectSearch(projectId: string) {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<ProjectSearchScope>("all");
  const [results, setResults] = useState<ProjectSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const normalized = query.trim();
    if (!normalized) {
      setResults([]);
      setIsLoading(false);
      return;
    }

    let isCancelled = false;
    setIsLoading(true);
    const timer = window.setTimeout(() => {
      void searchProject(projectId, normalized, scope)
        .then((response) => {
          if (!isCancelled) {
            setResults(response.results);
          }
        })
        .catch(() => {
          if (!isCancelled) {
            setResults([]);
          }
        })
        .finally(() => {
          if (!isCancelled) {
            setIsLoading(false);
          }
        });
    }, 280);

    return () => {
      isCancelled = true;
      window.clearTimeout(timer);
    };
  }, [projectId, query, scope]);

  const groups = useMemo<ProjectSearchGroup[]>(() => {
    return groupOrder
      .map((key) => ({
        key,
        label: groupLabels[key],
        results: results.filter((result) => result.resource_type === key),
      }))
      .filter((group) => group.results.length > 0);
  }, [results]);

  return {
    groups,
    isLoading,
    query,
    results,
    scope,
    setQuery,
    setScope,
  } satisfies ProjectSearchApi;
}
