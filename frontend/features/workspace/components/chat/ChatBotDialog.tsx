"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { MessageCircle, Plus, Trash2, X } from "lucide-react";
import type { ChatMessage, ChatSessionSummary } from "@/lib/api/types";
import { ChatComposer } from "./ChatComposer";
import { ChatMessages } from "./ChatMessages";
import { ChatSessionSidebar } from "./ChatSessionSidebar";
import "./ChatBotDialog.css";

type ChatBotDialogProps = {
  messages: ChatMessage[];
  isLoading: boolean;
  isSessionsLoading: boolean;
  error: string | null;
  chapterId?: string;
  sessions: ChatSessionSummary[];
  activeSessionId: string | null;
  onCreateSession: () => void;
  onSelectSession: (id: string) => Promise<void>;
  onRenameSession: (id: string, title: string) => Promise<void>;
  onDeleteSession: (id: string) => Promise<void>;
  onSend: (content: string, chapterId?: string) => void;
  onClose: () => void;
  onClear: () => void;
};

type ResizeDir = "n" | "s" | "e" | "w" | "ne" | "nw" | "se" | "sw";

const DEFAULT_WIDTH = 760;
const DEFAULT_HEIGHT = 1040;
const MIN_WIDTH = 260;
const MAX_WIDTH = 1200;
const MIN_HEIGHT = 200;
const MAX_HEIGHT = 1200;

function initialLeft(): number {
  if (typeof window === "undefined") return 0;
  return Math.max(0, (window.innerWidth - DEFAULT_WIDTH) / 2);
}

function initialTop(): number {
  if (typeof window === "undefined") return 0;
  return Math.max(0, (window.innerHeight - DEFAULT_HEIGHT) / 2);
}

export function ChatBotDialog({
  messages,
  isLoading,
  isSessionsLoading,
  error,
  chapterId,
  sessions,
  activeSessionId,
  onCreateSession,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
  onSend,
  onClose,
  onClear,
}: ChatBotDialogProps) {
  const [left, setLeft] = useState(initialLeft);
  const [top, setTop] = useState(initialTop);
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [height, setHeight] = useState(DEFAULT_HEIGHT);
  const [resizeDir, setResizeDir] = useState<ResizeDir | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef({
    startX: 0,
    startY: 0,
    startLeft: 0,
    startTop: 0,
    startWidth: 0,
    startHeight: 0,
  });
  const busy = resizeDir !== null || isDragging;

  const onResizePointerDown = useCallback(
    (dir: ResizeDir) => (event: React.PointerEvent) => {
      event.preventDefault();
      event.stopPropagation();
      setResizeDir(dir);
      dragRef.current = {
        startX: event.clientX,
        startY: event.clientY,
        startLeft: left,
        startTop: top,
        startWidth: width,
        startHeight: height,
      };
    },
    [height, left, top, width],
  );

  useEffect(() => {
    if (!resizeDir) return;

    const handleMove = (event: PointerEvent) => {
      event.preventDefault();
      const dx = event.clientX - dragRef.current.startX;
      const dy = event.clientY - dragRef.current.startY;
      const { startLeft, startTop, startWidth, startHeight } = dragRef.current;
      let nextLeft = startLeft;
      let nextTop = startTop;
      let nextWidth = startWidth;
      let nextHeight = startHeight;

      if (resizeDir.includes("e")) {
        nextWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startWidth + dx));
      }
      if (resizeDir.includes("w")) {
        nextWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startWidth - dx));
        nextLeft = startLeft + (startWidth - nextWidth);
      }
      if (resizeDir.includes("s")) {
        nextHeight = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, startHeight + dy));
      }
      if (resizeDir.includes("n")) {
        nextHeight = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, startHeight - dy));
        nextTop = startTop + (startHeight - nextHeight);
      }

      setLeft(nextLeft);
      setTop(nextTop);
      setWidth(nextWidth);
      setHeight(nextHeight);
    };
    const handleUp = () => setResizeDir(null);
    document.addEventListener("pointermove", handleMove);
    document.addEventListener("pointerup", handleUp);
    return () => {
      document.removeEventListener("pointermove", handleMove);
      document.removeEventListener("pointerup", handleUp);
    };
  }, [resizeDir]);

  const handleDragStart = useCallback(
    (event: React.PointerEvent) => {
      event.preventDefault();
      setIsDragging(true);
      dragRef.current = {
        ...dragRef.current,
        startX: event.clientX,
        startY: event.clientY,
        startLeft: left,
        startTop: top,
      };
    },
    [left, top],
  );

  useEffect(() => {
    if (!isDragging) return;
    const handleMove = (event: PointerEvent) => {
      event.preventDefault();
      setLeft(dragRef.current.startLeft + (event.clientX - dragRef.current.startX));
      setTop(dragRef.current.startTop + (event.clientY - dragRef.current.startY));
    };
    const handleUp = () => setIsDragging(false);
    document.addEventListener("pointermove", handleMove);
    document.addEventListener("pointerup", handleUp);
    return () => {
      document.removeEventListener("pointermove", handleMove);
      document.removeEventListener("pointerup", handleUp);
    };
  }, [isDragging]);

  return (
    <div
      className="chat-bot-dialog"
      style={{
        height,
        left,
        top,
        userSelect: busy ? "none" : undefined,
        width,
      }}
    >
      {(["n", "s", "e", "w", "ne", "nw", "se", "sw"] as ResizeDir[]).map((dir) => (
        <div
          className={`chat-bot-resize-${dir}`}
          key={dir}
          onPointerDown={onResizePointerDown(dir)}
        />
      ))}

      <div
        className="chat-bot-header"
        onPointerDown={handleDragStart}
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
      >
        <div className="chat-bot-header-title">
          <MessageCircle size={16} />
          <span>聊聊作品</span>
        </div>
        <div className="chat-bot-header-actions">
          <button
            className="chat-bot-header-btn"
            onClick={() => {
              onCreateSession();
            }}
            title="新建对话"
            type="button"
          >
            <Plus size={14} />
          </button>
          <button
            className="chat-bot-header-btn"
            disabled={messages.length === 0}
            onClick={onClear}
            title="清空当前显示"
            type="button"
          >
            <Trash2 size={14} />
          </button>
          <button className="chat-bot-header-btn" onClick={onClose} title="关闭" type="button">
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="chat-bot-body">
        <ChatSessionSidebar
          activeSessionId={activeSessionId}
          isSessionsLoading={isSessionsLoading}
          onDeleteSession={onDeleteSession}
          onRenameSession={onRenameSession}
          onSelectSession={onSelectSession}
          sessions={sessions}
        />
        <div className="chat-bot-main">
          <ChatMessages error={error} isLoading={isLoading} messages={messages} />
          <ChatComposer chapterId={chapterId} isLoading={isLoading} onSend={onSend} />
        </div>
      </div>
    </div>
  );
}
