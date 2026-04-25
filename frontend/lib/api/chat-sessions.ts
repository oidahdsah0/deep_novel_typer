import { apiFetch } from "./client";
import type {
  ChatSessionSummary,
  ChatSessionWithMessages,
  CreateChatSessionInput,
  UpdateChatSessionInput,
} from "./types/index";

export async function listChatSessions(
  projectId: string,
): Promise<ChatSessionSummary[]> {
  return apiFetch<ChatSessionSummary[]>(
    `/api/projects/${encodeURIComponent(projectId)}/chat/sessions`,
  );
}

export async function createChatSession(
  projectId: string,
  input?: CreateChatSessionInput,
): Promise<ChatSessionWithMessages> {
  return apiFetch<ChatSessionWithMessages>(
    `/api/projects/${encodeURIComponent(projectId)}/chat/sessions`,
    {
      method: "POST",
      body: JSON.stringify(input ?? { title: "新对话" }),
    },
  );
}

export async function getChatSession(
  projectId: string,
  sessionId: string,
): Promise<ChatSessionWithMessages> {
  return apiFetch<ChatSessionWithMessages>(
    `/api/projects/${encodeURIComponent(projectId)}/chat/sessions/${encodeURIComponent(sessionId)}`,
  );
}

export async function updateChatSession(
  projectId: string,
  sessionId: string,
  input: UpdateChatSessionInput,
): Promise<ChatSessionSummary> {
  return apiFetch<ChatSessionSummary>(
    `/api/projects/${encodeURIComponent(projectId)}/chat/sessions/${encodeURIComponent(sessionId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}

export async function deleteChatSession(
  projectId: string,
  sessionId: string,
): Promise<void> {
  return apiFetch<void>(
    `/api/projects/${encodeURIComponent(projectId)}/chat/sessions/${encodeURIComponent(sessionId)}`,
    { method: "DELETE" },
  );
}
