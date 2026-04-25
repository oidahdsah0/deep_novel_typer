"use client";

import { useCallback, useEffect, useRef } from "react";
import { streamChat } from "@/lib/api/chat";
import {
  appendAssistantDelta,
  appendAssistantReasoning,
  touchSessionInList,
  type ChatSessionsState,
} from "@/features/workspace/hooks/chatSessionState";
import type { ChatMessage } from "@/lib/api/types";
import type { Dispatch, MutableRefObject, SetStateAction } from "react";

type UseChatMessageSenderOptions = {
  projectId: string;
  setState: Dispatch<SetStateAction<ChatSessionsState>>;
  messagesRef: MutableRefObject<ChatMessage[]>;
  loadingRef: MutableRefObject<boolean>;
  activeSessionRef: MutableRefObject<string | null>;
};

export function useChatMessageSender({
  projectId,
  setState,
  messagesRef,
  loadingRef,
  activeSessionRef,
}: UseChatMessageSenderOptions) {
  const abortControllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);
  const activeSessionId = activeSessionRef.current;

  const cancelMessage = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    loadingRef.current = false;
    setState((prev) => ({ ...prev, isLoading: false }));
  }, [loadingRef, setState]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      loadingRef.current = false;
    };
  }, [loadingRef]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      loadingRef.current = false;
    };
  }, [activeSessionId, loadingRef]);

  const sendMessage = useCallback(
    async (content: string, chapterId?: string) => {
      const trimmed = content.trim();
      if (!trimmed || loadingRef.current) return;

      const sessionId = activeSessionRef.current;
      if (!sessionId) return;

      const userMessage: ChatMessage = { role: "user", content: trimmed };
      const history = [...messagesRef.current, userMessage];

      setState((prev) => ({
        ...prev,
        messages: history,
        isLoading: true,
        error: null,
      }));
      loadingRef.current = true;
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const shouldApplyUpdate = () =>
        mountedRef.current &&
        !controller.signal.aborted &&
        activeSessionRef.current === sessionId;

      await streamChat(
        projectId,
        {
          chapter_id: chapterId,
          session_id: sessionId,
          messages: history
            .filter(({ role, content }) => role === "user" || content.trim())
            .map(({ role, content }) => ({ role, content })),
        },
        (delta) => {
          if (!shouldApplyUpdate()) return;
          setState((prev) => ({
            ...prev,
            messages: appendAssistantDelta(prev.messages, delta),
          }));
        },
        (reasoningDelta) => {
          if (!shouldApplyUpdate()) return;
          setState((prev) => ({
            ...prev,
            messages: appendAssistantReasoning(
              prev.messages,
              reasoningDelta,
            ),
          }));
        },
        () => {
          if (!shouldApplyUpdate()) return;
          loadingRef.current = false;
          abortControllerRef.current = null;
          setState((prev) => ({
            ...prev,
            isLoading: false,
            sessions: touchSessionInList(
              prev.sessions,
              sessionId,
              new Date().toISOString(),
            ),
          }));
        },
        (err) => {
          if (!shouldApplyUpdate()) return;
          loadingRef.current = false;
          abortControllerRef.current = null;
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: err,
          }));
        },
        controller.signal,
      );
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
    },
    [activeSessionRef, loadingRef, messagesRef, projectId, setState],
  );

  return { cancelMessage, sendMessage };
}
