"use client";

import { MessageCircle, Sparkles, WandSparkles } from "lucide-react";

export function DraftQuickMenu({
  hasSelection,
  left,
  onBlueprint,
  onChat,
  onNextParagraph,
  onNextSection,
  onPolish,
  top,
  visible,
}: {
  hasSelection: boolean;
  left: number;
  onBlueprint: () => void;
  onChat: () => void;
  onNextParagraph: () => void;
  onNextSection: () => void;
  onPolish: () => void;
  top: number;
  visible: boolean;
}) {
  const className = [
    "draft-fab-menu",
    visible ? "visible" : "",
    hasSelection ? "expanded has-selection" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      aria-label="正文快捷操作"
      className={className}
      style={{ left, top }}
    >
      <button
        aria-expanded={hasSelection}
        className="draft-fab-trigger"
        type="button"
        aria-label="正文快捷菜单"
      >
        <WandSparkles size={18} />
      </button>
      <div className="draft-fab-actions">
        <button
          className={hasSelection ? "draft-fab-action polish active" : "draft-fab-action polish"}
          disabled={!hasSelection}
          onClick={onPolish}
          onMouseDown={(event) => event.preventDefault()}
          type="button"
        >
          <Sparkles size={15} />
          润色选中
        </button>
        <button
          className="draft-fab-action blueprint"
          onClick={onBlueprint}
          onMouseDown={(event) => event.preventDefault()}
          type="button"
        >
          <Sparkles size={15} />
          基础铺设
        </button>
        <button
          className="draft-fab-action chat"
          onClick={onChat}
          onMouseDown={(event) => event.preventDefault()}
          type="button"
        >
          <MessageCircle size={15} />
          聊聊作品
        </button>
        <button
          className="draft-fab-action"
          onClick={onNextParagraph}
          onMouseDown={(event) => event.preventDefault()}
          type="button"
        >
          <WandSparkles size={15} />
          生成下一段落
        </button>
        <button
          className="draft-fab-action"
          onClick={onNextSection}
          onMouseDown={(event) => event.preventDefault()}
          type="button"
        >
          <WandSparkles size={15} />
          生成下一部分
        </button>
      </div>
    </div>
  );
}
