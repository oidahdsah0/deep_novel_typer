"use client";

import { ChevronDown, ChevronRight, MessageCircle } from "lucide-react";
import MarkdownPreview from "@uiw/react-markdown-preview";
import rehypeSanitize from "rehype-sanitize";
import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "@/lib/api/types";

type ChatMessagesProps = {
  error: string | null;
  isLoading: boolean;
  messages: ChatMessage[];
};

function collapseNewlines(text: string): string {
  return text.replace(/\n{3,}/g, "\n\n");
}

export function ChatMessages({ error, isLoading, messages }: ChatMessagesProps) {
  const [expandedReasoning, setExpandedReasoning] = useState<Set<number>>(new Set());
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="chat-bot-messages" ref={listRef}>
      {messages.length === 0 && !isLoading ? (
        <div className="chat-bot-empty">
          <MessageCircle size={32} />
          <p>在创作过程中有什么想问的吗？</p>
          <p className="chat-bot-empty-sub">可以讨论角色、情节、设定或写作技巧</p>
        </div>
      ) : null}
      {messages.map((msg, index) => {
        const isLastAssistant = index === messages.length - 1 && msg.role === "assistant";
        const hasReasoning = msg.role === "assistant" && msg.reasoning;
        const isReasoningExpanded = expandedReasoning.has(index);
        const isStreamingReasoning =
          isLastAssistant && isLoading && hasReasoning && !msg.content;

        return (
          <div
            className={[
              "chat-bot-bubble",
              msg.role === "user" ? "user" : "assistant",
              isLastAssistant && isLoading && msg.content ? "streaming" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            key={index}
          >
            {hasReasoning ? (
              <div className="chat-bot-reasoning">
                <button
                  className="chat-bot-reasoning-toggle"
                  onClick={() => {
                    setExpandedReasoning((prev) => {
                      const next = new Set(prev);
                      if (next.has(index)) next.delete(index);
                      else next.add(index);
                      return next;
                    });
                  }}
                  type="button"
                >
                  {isReasoningExpanded || isStreamingReasoning ? (
                    <ChevronDown size={14} />
                  ) : (
                    <ChevronRight size={14} />
                  )}
                  <span>{isStreamingReasoning ? "思考中..." : "思考过程"}</span>
                </button>
                {isReasoningExpanded || isStreamingReasoning ? (
                  <div className="chat-bot-reasoning-content">{msg.reasoning}</div>
                ) : null}
              </div>
            ) : null}
            {msg.content ? (
              <div className="chat-bot-content">
                {msg.role === "assistant" ? (
                  <div className="chat-bot-markdown" data-color-mode="light">
                    <MarkdownPreview
                      rehypePlugins={[rehypeSanitize]}
                      source={collapseNewlines(msg.content)}
                    />
                  </div>
                ) : (
                  msg.content
                )}
              </div>
            ) : null}
          </div>
        );
      })}
      {isLoading && messages[messages.length - 1]?.role !== "assistant" ? (
        <div className="chat-bot-bubble assistant loading">
          <span className="chat-bot-dot-pulse" />
        </div>
      ) : null}
      {error ? <div className="chat-bot-error">{error}</div> : null}
    </div>
  );
}
