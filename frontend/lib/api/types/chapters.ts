import type { ProjectSummary } from "./projects";

export type ChapterDocxExportInput = {
  chapter_ids: string[];
};

export type ChapterSummary = {
  id: string;
  title: string;
  order: number;
  word_count: number;
};

export type ChapterDetail = ChapterSummary & {
  content: string;
  writing_synopsis: string;
  writing_synopsis_updated_at: string;
  updated_at: string;
};

export type ChapterSaveResponse = ChapterDetail & {
  project: ProjectSummary;
};

export type ChapterWritingSynopsisSaveResponse = ChapterDetail & {
  project: ProjectSummary;
};

export type ChapterNodeType = "folder" | "chapter";

export type ChapterNode = {
  id: string;
  parent_id: string | null;
  type: ChapterNodeType;
  title: string;
  chapter_id: string | null;
  word_count: number;
  updated_at: string;
  children: ChapterNode[];
};

export type ChapterSearchMatch = {
  field: "title" | "content";
  snippet: string;
};

export type ChapterSearchResult = {
  chapter_id: string;
  node_id: string;
  title: string;
  path: string[];
  word_count: number;
  score: number;
  matches: ChapterSearchMatch[];
};

export type ChapterSearchResponse = {
  query: string;
  results: ChapterSearchResult[];
};

export type CreateChapterNodeInput = {
  type: ChapterNodeType;
  title: string;
  parent_id?: string | null;
  content?: string;
};

export type UpdateChapterNodeInput = {
  title?: string;
};

export type MoveTreeNodeInput = {
  parent_id?: string | null;
  before_node_id?: string | null;
};

export type MoveChapterNodeResponse = {
  chapter_tree: ChapterNode[];
  chapters: ChapterSummary[];
};
