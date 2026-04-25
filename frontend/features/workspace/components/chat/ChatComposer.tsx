"use client";

import { SendHorizonal } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

type ChatComposerProps = {
  chapterId?: string;
  isLoading: boolean;
  onSend: (content: string, chapterId?: string) => void;
};

export function ChatComposer({ chapterId, isLoading, onSend }: ChatComposerProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isLoading]);

  const handleSend = useCallback(() => {
    if (!input.trim() || isLoading) return;
    onSend(input.trim(), chapterId);
    setInput("");
  }, [chapterId, input, isLoading, onSend]);

  return (
    <div className="chat-bot-input-area">
      <textarea
        className="chat-bot-input"
        disabled={isLoading}
        onChange={(event) => setInput(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSend();
          }
        }}
        placeholder="输入消息..."
        ref={inputRef}
        rows={1}
        value={input}
      />
      <button
        className="chat-bot-send-btn"
        disabled={!input.trim() || isLoading}
        onClick={handleSend}
        type="button"
      >
        <SendHorizonal size={18} />
      </button>
    </div>
  );
}
