"use client";

import type { ChatMessage, ChatSessionSummary } from "@/lib/api/types";

export type ChatSessionsState = {
  sessions: ChatSessionSummary[];
  activeSessionId: string | null;
  messages: ChatMessage[];
  isOpen: boolean;
  isLoading: boolean;
  isSessionsLoading: boolean;
  error: string | null;
};

export function errorMessage(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback;
}

export function appendAssistantDelta(messages: ChatMessage[], delta: string) {
  const next = [...messages];
  const last = next[next.length - 1];
  if (last?.role === "assistant") {
    next[next.length - 1] = { ...last, content: last.content + delta };
  } else {
    next.push({ role: "assistant", content: delta });
  }
  return next;
}

export function appendAssistantReasoning(
  messages: ChatMessage[],
  reasoningDelta: string,
) {
  const next = [...messages];
  const last = next[next.length - 1];
  if (last?.role === "assistant") {
    next[next.length - 1] = {
      ...last,
      reasoning: (last.reasoning ?? "") + reasoningDelta,
    };
  } else {
    next.push({
      role: "assistant",
      content: "",
      reasoning: reasoningDelta,
    });
  }
  return next;
}

export function renameSessionInList(
  sessions: ChatSessionSummary[],
  sessionId: string,
  title: string,
  updatedAt: string,
) {
  return sessions.map((session) =>
    session.id === sessionId
      ? { ...session, title, updated_at: updatedAt }
      : session,
  );
}

export function touchSessionInList(
  sessions: ChatSessionSummary[],
  sessionId: string,
  updatedAt: string,
) {
  return sessions.map((session) =>
    session.id === sessionId
      ? { ...session, updated_at: updatedAt }
      : session,
  );
}
