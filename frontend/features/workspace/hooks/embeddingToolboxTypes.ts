import type { ApiConfig } from "@/lib/api/index";
import type { ActiveResource, ChapterSelection } from "@/features/workspace/types";

export type EmbeddingToolboxTab = "heatmap" | "clusters" | "tags" | "settings";
export type EmbeddingRangeMode = "full" | "selection";

export type EmbeddingToolboxOptions = {
  activeSelection: ChapterSelection | null;
  apiConfigs: ApiConfig[];
  content: string;
  projectId: string;
  resource: ActiveResource;
};
