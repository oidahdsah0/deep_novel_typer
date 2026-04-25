"use client";

import { Columns2, Eye, PenLine, Sparkles, WandSparkles } from "lucide-react";
import dynamic from "next/dynamic";
import { useRef } from "react";
import rehypeSanitize from "rehype-sanitize";
import type { ChapterSelection, MarkdownViewMode } from "../../types";

const MDEditor = dynamic(() => import("@uiw/react-md-editor"), { ssr: false });

export function MarkdownDocumentPane({
  content,
  hasSelection,
  mode,
  onChange,
  onContinue,
  onModeChange,
  onPolishSelection,
  onSelectionChange,
}: {
  content: string;
  hasSelection: boolean;
  mode: MarkdownViewMode;
  onChange: (content: string) => void;
  onContinue: () => void;
  onModeChange: (mode: MarkdownViewMode) => void;
  onPolishSelection: () => void;
  onSelectionChange: (selection: ChapterSelection | null) => void;
}) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const previewMode = mode === "split" ? "live" : mode === "preview" ? "preview" : "edit";

  function readSelection() {
    const textarea = rootRef.current?.querySelector("textarea");
    if (!textarea || mode === "preview") {
      onSelectionChange(null);
      return;
    }
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    if (end <= start) {
      onSelectionChange(null);
      return;
    }
    const text = textarea.value.slice(start, end);
    onSelectionChange(text.trim() ? { start, end, text } : null);
  }

  return (
    <div className="markdown-document-pane" data-color-mode="light" ref={rootRef}>
      <div className="markdown-toolbar">
        <div className="markdown-mode-switch" aria-label="Markdown 视图模式">
          <button
            className={mode === "edit" ? "active" : ""}
            onClick={() => onModeChange("edit")}
            type="button"
          >
            <PenLine size={15} />
            编辑
          </button>
          <button
            className={mode === "split" ? "active" : ""}
            onClick={() => onModeChange("split")}
            type="button"
          >
            <Columns2 size={15} />
            对照
          </button>
          <button
            className={mode === "preview" ? "active" : ""}
            onClick={() => onModeChange("preview")}
            type="button"
          >
            <Eye size={15} />
            浏览
          </button>
        </div>
        <div className="markdown-ai-actions">
          <button
            className="secondary-button compact-action"
            disabled={!hasSelection}
            onClick={onPolishSelection}
            type="button"
          >
            <Sparkles size={15} />
            润色选区
          </button>
          <button className="secondary-button compact-action" onClick={onContinue} type="button">
            <WandSparkles size={15} />
            生成后续
          </button>
        </div>
      </div>
      <MDEditor
        className="markdown-editor"
        height="100%"
        hideToolbar={mode === "preview"}
        onChange={(value) => {
          onChange(value ?? "");
          onSelectionChange(null);
        }}
        preview={previewMode}
        previewOptions={{ rehypePlugins: [[rehypeSanitize]] }}
        textareaProps={{
          onKeyUp: readSelection,
          onMouseUp: readSelection,
          onSelect: readSelection,
          spellCheck: false,
        }}
        value={content}
        visibleDragbar={false}
      />
    </div>
  );
}
