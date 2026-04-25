"use client";

import { Check, MessageCircle, Pencil, Trash2, X } from "lucide-react";
import { useCallback, useState } from "react";
import type { ChatSessionSummary } from "@/lib/api/types";

type ChatSessionSidebarProps = {
  activeSessionId: string | null;
  isSessionsLoading: boolean;
  sessions: ChatSessionSummary[];
  onDeleteSession: (id: string) => Promise<void>;
  onRenameSession: (id: string, title: string) => Promise<void>;
  onSelectSession: (id: string) => Promise<void>;
};

export function ChatSessionSidebar({
  activeSessionId,
  isSessionsLoading,
  sessions,
  onDeleteSession,
  onRenameSession,
  onSelectSession,
}: ChatSessionSidebarProps) {
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const handleRenameCommit = useCallback(
    (sessionId: string) => {
      if (renameDraft.trim()) {
        onRenameSession(sessionId, renameDraft.trim());
      }
      setRenamingSessionId(null);
    },
    [renameDraft, onRenameSession],
  );

  return (
    <aside className="chat-bot-sidebar">
      <div className="chat-bot-sidebar-title">历史对话</div>
      {isSessionsLoading ? (
        <div className="chat-bot-sidebar-status">加载中...</div>
      ) : sessions.length === 0 ? (
        <div className="chat-bot-sidebar-status">暂无对话</div>
      ) : (
        <div className="chat-bot-sidebar-list">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={[
                "chat-bot-sidebar-item",
                session.id === activeSessionId ? "active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {renamingSessionId === session.id ? (
                <input
                  autoFocus
                  className="chat-bot-sidebar-rename-input"
                  onBlur={() => handleRenameCommit(session.id)}
                  onChange={(event) => setRenameDraft(event.target.value)}
                  onClick={(event) => event.stopPropagation()}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") handleRenameCommit(session.id);
                    if (event.key === "Escape") setRenamingSessionId(null);
                  }}
                  type="text"
                  value={renameDraft}
                />
              ) : (
                <button
                  className="chat-bot-sidebar-item-btn"
                  onClick={() => onSelectSession(session.id)}
                  title={session.title}
                  type="button"
                >
                  <MessageCircle size={12} />
                  <span>{session.title}</span>
                </button>
              )}
              <div className="chat-bot-sidebar-item-actions">
                <button
                  aria-label={`重命名 ${session.title}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    setRenamingSessionId(session.id);
                    setRenameDraft(session.title);
                  }}
                  title="重命名"
                  type="button"
                >
                  <Pencil size={10} />
                </button>
                {confirmDeleteId === session.id ? (
                  <>
                    <button
                      aria-label="确认删除"
                      onClick={(event) => {
                        event.stopPropagation();
                        onDeleteSession(session.id);
                        setConfirmDeleteId(null);
                      }}
                      title="确认删除"
                      type="button"
                    >
                      <Check size={10} />
                    </button>
                    <button
                      aria-label="取消删除"
                      onClick={(event) => {
                        event.stopPropagation();
                        setConfirmDeleteId(null);
                      }}
                      title="取消"
                      type="button"
                    >
                      <X size={10} />
                    </button>
                  </>
                ) : (
                  <button
                    aria-label={`删除 ${session.title}`}
                    onClick={(event) => {
                      event.stopPropagation();
                      setConfirmDeleteId(session.id);
                    }}
                    title="删除"
                    type="button"
                  >
                    <Trash2 size={10} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
