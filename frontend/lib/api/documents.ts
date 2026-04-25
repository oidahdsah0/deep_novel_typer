import { apiFetch } from "./client";
import type {
  CreateDocumentNodeInput,
  DocumentDetail,
  DocumentNode,
  DocumentSaveResponse,
  MoveDocumentNodeResponse,
  MoveTreeNodeInput,
  UpdateDocumentNodeInput
} from "./types/index";

export async function getDocument(projectId: string, documentId: string) {
  return await apiFetch<DocumentDetail>(
    `/api/projects/${encodeURIComponent(projectId)}/documents/${encodeURIComponent(documentId)}`,
  );
}

export async function saveDocument(
  projectId: string,
  documentId: string,
  content: string,
  baseUpdatedAt?: string | null,
) {
  return await apiFetch<DocumentSaveResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/documents/${encodeURIComponent(documentId)}`,
    {
      method: "PUT",
      body: JSON.stringify({ content, base_updated_at: baseUpdatedAt ?? null }),
    },
  );
}

export async function createDocumentNode(
  projectId: string,
  input: CreateDocumentNodeInput,
): Promise<DocumentNode> {
  return await apiFetch<DocumentNode>(
    `/api/projects/${encodeURIComponent(projectId)}/documents/nodes`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function updateDocumentNode(
  projectId: string,
  nodeId: string,
  input: UpdateDocumentNodeInput,
): Promise<DocumentNode> {
  return await apiFetch<DocumentNode>(
    `/api/projects/${encodeURIComponent(projectId)}/documents/nodes/${encodeURIComponent(nodeId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}

export async function moveDocumentNode(
  projectId: string,
  nodeId: string,
  input: MoveTreeNodeInput,
): Promise<MoveDocumentNodeResponse> {
  return await apiFetch<MoveDocumentNodeResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/documents/nodes/${encodeURIComponent(nodeId)}/move`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}

export async function deleteDocumentNode(projectId: string, nodeId: string): Promise<void> {
  await apiFetch<void>(
    `/api/projects/${encodeURIComponent(projectId)}/documents/nodes/${encodeURIComponent(nodeId)}`,
    {
      method: "DELETE",
    },
  );
}
