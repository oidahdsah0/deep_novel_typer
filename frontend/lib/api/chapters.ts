import { apiFetch, apiFetchBlob } from "./client";
import type {
  ChapterDocxExportInput,
  ChapterDetail,
  ChapterNode,
  ChapterSaveResponse,
  ChapterSearchResponse,
  ChapterWritingSynopsisSaveResponse,
  CreateChapterNodeInput,
  MoveChapterNodeResponse,
  MoveTreeNodeInput,
  UpdateChapterNodeInput
} from "./types/index";

export async function createChapter(
  projectId: string,
  title: string,
  parentId: string | null = null,
): Promise<ChapterDetail> {
  return await apiFetch<ChapterDetail>(
    `/api/projects/${encodeURIComponent(projectId)}/chapters`,
    {
      method: "POST",
      body: JSON.stringify({ title, content: "", parent_id: parentId }),
    },
  );
}

export async function saveChapter(
  projectId: string,
  chapterId: string,
  content: string,
  baseUpdatedAt?: string | null,
): Promise<ChapterSaveResponse> {
  return await apiFetch<ChapterSaveResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}`,
    {
      method: "PUT",
      body: JSON.stringify({ content, base_updated_at: baseUpdatedAt ?? null }),
    },
  );
}

export async function saveChapterWritingSynopsis(
  projectId: string,
  chapterId: string,
  writingSynopsis: string,
  baseUpdatedAt?: string | null,
): Promise<ChapterWritingSynopsisSaveResponse> {
  return await apiFetch<ChapterWritingSynopsisSaveResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/writing-synopsis`,
    {
      method: "PUT",
      body: JSON.stringify({
        writing_synopsis: writingSynopsis,
        base_updated_at: baseUpdatedAt ?? null,
      }),
    },
  );
}

export async function createChapterNode(
  projectId: string,
  input: CreateChapterNodeInput,
): Promise<ChapterNode> {
  return await apiFetch<ChapterNode>(
    `/api/projects/${encodeURIComponent(projectId)}/chapters/nodes`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function updateChapterNode(
  projectId: string,
  nodeId: string,
  input: UpdateChapterNodeInput,
): Promise<ChapterNode> {
  return await apiFetch<ChapterNode>(
    `/api/projects/${encodeURIComponent(projectId)}/chapters/nodes/${encodeURIComponent(nodeId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}

export async function moveChapterNode(
  projectId: string,
  nodeId: string,
  input: MoveTreeNodeInput,
): Promise<MoveChapterNodeResponse> {
  return await apiFetch<MoveChapterNodeResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/chapters/nodes/${encodeURIComponent(nodeId)}/move`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}

export async function deleteChapterNode(projectId: string, nodeId: string): Promise<void> {
  await apiFetch<void>(
    `/api/projects/${encodeURIComponent(projectId)}/chapters/nodes/${encodeURIComponent(nodeId)}`,
    {
      method: "DELETE",
    },
  );
}

export async function searchChapters(
  projectId: string,
  query: string,
  limit = 30,
): Promise<ChapterSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return await apiFetch<ChapterSearchResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/chapters/search?${params.toString()}`,
  );
}

export async function exportChaptersDocx(
  projectId: string,
  input: ChapterDocxExportInput,
): Promise<Blob> {
  return await apiFetchBlob(
    `/api/projects/${encodeURIComponent(projectId)}/chapters/export-docx`,
    {
      method: "POST",
      body: JSON.stringify(input),
      headers: {
        Accept: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Content-Type": "application/json",
      },
    },
  );
}
