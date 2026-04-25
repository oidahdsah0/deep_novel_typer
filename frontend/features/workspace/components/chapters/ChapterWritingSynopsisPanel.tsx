"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import type { ChapterWritingSynopsisApi } from "../../hooks/useChapterWritingSynopsis";

export function ChapterWritingSynopsisPanel({
  synopsis,
}: {
  synopsis: ChapterWritingSynopsisApi;
}) {
  return (
    <section className="chapter-synopsis-panel" aria-label="写作梗概">
      <header
        className={
          synopsis.isCollapsed
            ? "chapter-synopsis-heading rail-collapsible-heading collapsed"
            : "chapter-synopsis-heading rail-collapsible-heading"
        }
      >
        <button
          aria-expanded={!synopsis.isCollapsed}
          className="rail-section-toggle"
          onClick={() => synopsis.setIsCollapsed(!synopsis.isCollapsed)}
          type="button"
        >
          {synopsis.isCollapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
          <span className="rail-section-toggle-copy">
            <span className="eyebrow">Chapter Synopsis</span>
            <span className="rail-section-title">写作梗概</span>
          </span>
        </button>
        <small>{saveStateLabel(synopsis.saveState)}</small>
      </header>
      {synopsis.isCollapsed ? null : (
        <textarea
          className="chapter-synopsis-editor"
          maxLength={60000}
          onBlur={() => void synopsis.flush().catch(() => undefined)}
          onChange={(event) => synopsis.setDraft(event.target.value)}
          value={synopsis.draft}
        />
      )}
    </section>
  );
}

function saveStateLabel(saveState: ChapterWritingSynopsisApi["saveState"]) {
  if (saveState === "saving") return "保存中";
  if (saveState === "conflict") return "冲突";
  if (saveState === "error") return "保存失败";
  return "已保存";
}
