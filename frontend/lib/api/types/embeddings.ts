export type EmbeddingDistanceAlgorithm = "cosine" | "euclidean" | "manhattan";
export type EmbeddingSegmentationMode = "word" | "sentence";
export type EmbeddingResourceType = "chapter" | "document";
export type EmbeddingClusterMode = "fixed_tag_centers";

export type EmbeddingTag = {
  id: string;
  project_id: string;
  name: string;
  description: string;
  color: string;
  is_enabled: boolean;
  embedding_config_id: string | null;
  embedding_model_signature: string | null;
  embedding_vector_ref: string | null;
  created_at: string;
  updated_at: string;
};

export type EmbeddingTagInput = {
  name: string;
  description?: string;
  color?: string;
  is_enabled?: boolean;
};

export type EmbeddingTagUpdate = Partial<EmbeddingTagInput>;

export type EmbeddingProjectSettings = {
  project_id: string;
  api_config_id: string | null;
  segmentation_mode: EmbeddingSegmentationMode;
  segment_size: number;
  algorithm: EmbeddingDistanceAlgorithm;
  updated_at: string | null;
};

export type EmbeddingProjectSettingsUpdate = {
  api_config_id?: string | null;
  segmentation_mode: EmbeddingSegmentationMode;
  segment_size: number;
  algorithm: EmbeddingDistanceAlgorithm;
};

export type EmbeddingTextRange = {
  start_offset: number | null;
  end_offset: number | null;
};

export type HeatmapRequest = {
  resource_type: EmbeddingResourceType;
  resource_id: string;
  api_config_id?: string | null;
  segmentation_mode: EmbeddingSegmentationMode;
  segment_size: number;
  algorithm: EmbeddingDistanceAlgorithm;
  tag_ids: string[];
  range?: EmbeddingTextRange | null;
  force_reembed?: boolean;
};

export type EmbeddingCacheStats = {
  requested_count: number;
  unique_count: number;
  cache_hit_count: number;
  cache_miss_count: number;
};

export type HeatmapTagScore = {
  raw_score: number | null;
  raw_distance: number | null;
  closeness: number;
};

export type HeatmapItem = {
  token_index: number;
  text: string;
  normalized_text: string;
  start_offset: number;
  end_offset: number;
  scores: Record<string, HeatmapTagScore>;
  nearest_tag_id: string | null;
};

export type HeatmapResponse = {
  run_id: string;
  status: string;
  resource_type: EmbeddingResourceType;
  resource_id: string;
  model_signature: string;
  model_signature_hash: string;
  segmentation_mode: EmbeddingSegmentationMode;
  segment_size: number;
  algorithm: EmbeddingDistanceAlgorithm;
  tags: EmbeddingTag[];
  items: HeatmapItem[];
  token_cache: EmbeddingCacheStats;
  tag_cache: EmbeddingCacheStats;
  warnings: string[];
};

export type ClusterRequest = {
  resource_type: EmbeddingResourceType;
  resource_id: string;
  api_config_id?: string | null;
  segmentation_mode: EmbeddingSegmentationMode;
  segment_size: number;
  algorithm: EmbeddingDistanceAlgorithm;
  cluster_mode: EmbeddingClusterMode;
  tag_ids: string[];
  range?: EmbeddingTextRange | null;
  force_reembed?: boolean;
};

export type ClusterPoint = {
  token_index: number;
  text: string;
  normalized_text: string;
  start_offset: number;
  end_offset: number;
  cluster_id: string;
  tag_id: string;
  raw_score: number | null;
  raw_distance: number | null;
  closeness: number;
  x: number;
  y: number;
};

export type ClusterSummary = {
  cluster_id: string;
  tag_id: string;
  name: string;
  color: string;
  point_count: number;
  average_closeness: number | null;
  x: number;
  y: number;
};

export type ClusterTagAnchor = {
  tag_id: string;
  name: string;
  color: string;
  x: number;
  y: number;
};

export type ClusterResponse = {
  run_id: string;
  status: string;
  resource_type: EmbeddingResourceType;
  resource_id: string;
  model_signature: string;
  model_signature_hash: string;
  segmentation_mode: EmbeddingSegmentationMode;
  segment_size: number;
  algorithm: EmbeddingDistanceAlgorithm;
  cluster_mode: EmbeddingClusterMode;
  projection: "pca";
  tags: EmbeddingTag[];
  points: ClusterPoint[];
  clusters: ClusterSummary[];
  tag_anchors: ClusterTagAnchor[];
  token_cache: EmbeddingCacheStats;
  tag_cache: EmbeddingCacheStats;
  warnings: string[];
};
