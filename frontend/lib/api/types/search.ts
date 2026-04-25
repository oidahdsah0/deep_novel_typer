import type { ProjectSearchResourceType, ProjectSearchScope } from "./common";

export type ProjectSearchMatch = {
  field: "title" | "path" | "content";
  snippet: string;
};

export type ProjectSearchResult = {
  resource_type: ProjectSearchResourceType;
  resource_id: string;
  resource_subtype: string;
  title: string;
  path: string[];
  updated_at: string;
  score: number;
  matches: ProjectSearchMatch[];
  metadata: Record<string, unknown>;
};

export type ProjectSearchResponse = {
  query: string;
  scope: ProjectSearchScope;
  results: ProjectSearchResult[];
};
