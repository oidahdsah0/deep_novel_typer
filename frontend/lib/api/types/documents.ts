import type { ProjectSummary } from "./projects";

export type WorkspaceDocument = {
  kind: "outline" | "design" | "note";
  title: string;
  updated_at: string;
};

export type DocumentNodeType = "folder" | "markdown";

export type DocumentNode = {
  id: string;
  parent_id: string | null;
  type: DocumentNodeType;
  title: string;
  updated_at: string;
  children: DocumentNode[];
};

export type MarkdownDocumentDetail = {
  id: string;
  parent_id: string | null;
  type: "markdown";
  title: string;
  updated_at: string;
  content: string;
};

export type DocumentDetail = MarkdownDocumentDetail;

export type DocumentSaveResponse = DocumentDetail & {
  project: ProjectSummary;
};

export type CreateDocumentNodeInput = {
  type: DocumentNodeType;
  title: string;
  parent_id?: string | null;
  content?: string;
};

export type UpdateDocumentNodeInput = {
  title?: string;
};

export type MoveDocumentNodeResponse = {
  document_tree: DocumentNode[];
};
