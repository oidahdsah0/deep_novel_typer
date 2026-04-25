"use client";

import { useCallback, useRef, useState } from "react";
import {
  listChatSessions,
  createChatSession,
  getChatSession,
  updateChatSession,
  deleteChatSession,
} from "@/lib/api/chat-sessions";
import {
  errorMessage,
  renameSessionInList,
  type ChatSessionsState,
} from "@/features/workspace/hooks/chatSessionState";
import { useChatMessageSender } from "@/features/workspace/hooks/useChatMessageSender";
import type { ChatSessionsApi } from "./workspaceToolApiTypes";

export type { ChatSessionsApi } from "./workspaceToolApiTypes";

export function useChatSessions(projectId: string) {
  const [state, setState] = useState<ChatSessionsState>({
    sessions: [],
    activeSessionId: null,
    messages: [],
    isOpen: false,
    isLoading: false,
    isSessionsLoading: false,
    error: null,
  });

  const messagesRef = useRef(state.messages);
  messagesRef.current = state.messages;
  const loadingRef = useRef(false);
  const activeSessionRef = useRef(state.activeSessionId);
  activeSessionRef.current = state.activeSessionId;
  const creatingRef = useRef(false);
  const { cancelMessage, sendMessage } = useChatMessageSender({
    projectId,
    setState,
    messagesRef,
    loadingRef,
    activeSessionRef,
  });

  const loadSessions = useCallback(async () => {
    setState((prev) => ({ ...prev, isSessionsLoading: true, error: null }));
    try {
      const sessions = await listChatSessions(projectId);
      setState((prev) => ({ ...prev, sessions, isSessionsLoading: false }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isSessionsLoading: false,
        error: errorMessage(err, "加载对话列表失败"),
      }));
    }
  }, [projectId]);

  const openChat = useCallback(async () => {
    setState((prev) => ({ ...prev, isOpen: true, error: null }));
    await loadSessions();
    // Auto-create a session if none exist and no creation is in flight
    if (!activeSessionRef.current && !creatingRef.current) {
      creatingRef.current = true;
      try {
        const session = await createChatSession(projectId);
        setState((prev) => ({
          ...prev,
          sessions: [session, ...prev.sessions],
          activeSessionId: session.id,
          messages: session.messages,
        }));
      } catch (err) {
        setState((prev) => ({
          ...prev,
          error: errorMessage(err, "创建对话失败"),
        }));
      } finally {
        creatingRef.current = false;
      }
    }
  }, [loadSessions, projectId]);

  const closeChat = useCallback(() => {
    cancelMessage();
    setState((prev) => ({ ...prev, isOpen: false }));
  }, [cancelMessage]);

  const selectSession = useCallback(
    async (sessionId: string) => {
      cancelMessage();
      setState((prev) => ({ ...prev, isLoading: true, error: null }));
      try {
        const session = await getChatSession(projectId, sessionId);
        setState((prev) => ({
          ...prev,
          activeSessionId: sessionId,
          messages: session.messages,
          isLoading: false,
        }));
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: errorMessage(err, "加载对话失败"),
        }));
      }
    },
    [cancelMessage, projectId],
  );

  const renameSession = useCallback(
    async (sessionId: string, title: string) => {
      setState((prev) => ({ ...prev, error: null }));
      try {
        const updated = await updateChatSession(projectId, sessionId, {
          title,
        });
        setState((prev) => ({
          ...prev,
          sessions: renameSessionInList(
            prev.sessions,
            sessionId,
            updated.title,
            updated.updated_at,
          ),
        }));
      } catch (err) {
        setState((prev) => ({
          ...prev,
          error: errorMessage(err, "重命名失败"),
        }));
      }
    },
    [projectId],
  );

  const removeSession = useCallback(
    async (sessionId: string) => {
      if (activeSessionRef.current === sessionId) {
        cancelMessage();
      }
      setState((prev) => ({ ...prev, error: null }));
      try {
        await deleteChatSession(projectId, sessionId);
        setState((prev) => {
          const nextSessions = prev.sessions.filter(
            (s) => s.id !== sessionId,
          );
          const wasActive = prev.activeSessionId === sessionId;
          return {
            ...prev,
            sessions: nextSessions,
            activeSessionId: wasActive
              ? nextSessions[0]?.id ?? null
              : prev.activeSessionId,
            messages: wasActive ? [] : prev.messages,
          };
        });
      } catch (err) {
        setState((prev) => ({
          ...prev,
          error: errorMessage(err, "删除失败"),
        }));
      }
    },
    [activeSessionRef, cancelMessage, projectId],
  );

  const createSession = useCallback(
    async (activate: boolean = true) => {
      setState((prev) => ({ ...prev, error: null }));
      try {
        const session = await createChatSession(projectId);
        setState((prev) => ({
          ...prev,
          sessions: [session, ...prev.sessions],
        }));
        if (activate) {
          cancelMessage();
          setState((prev) => ({
            ...prev,
            activeSessionId: session.id,
            messages: [],
          }));
        }
        return session;
      } catch (err) {
        setState((prev) => ({
          ...prev,
          error: errorMessage(err, "创建对话失败"),
        }));
        return null;
      }
    },
    [cancelMessage, projectId],
  );

  const clearMessages = useCallback(() => {
    setState((prev) => ({ ...prev, messages: [], error: null }));
  }, []);

  return {
    sessions: state.sessions,
    activeSessionId: state.activeSessionId,
    messages: state.messages,
    isOpen: state.isOpen,
    isLoading: state.isLoading,
    isSessionsLoading: state.isSessionsLoading,
    error: state.error,
    openChat,
    closeChat,
    sendMessage,
    clearMessages,
    loadSessions,
    createSession,
    selectSession,
    renameSession,
    removeSession,
  } satisfies ChatSessionsApi;
}
