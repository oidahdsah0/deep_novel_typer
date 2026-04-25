"use client";

import { maxRecentChapterCount } from "../../constants";
import { normalizeRecentChapterCount } from "../../promptProfileConfig";
import type { PromptMaterialOption, PromptProfileDraft } from "../../types";

export function ChapterPromptMaterialPanel({
  draft,
  onChangeDraft,
  onToggleChapter,
  options,
}: {
  draft: PromptProfileDraft;
  onChangeDraft: (patch: Partial<PromptProfileDraft>) => void;
  onToggleChapter: (chapterId: string) => void;
  options: PromptMaterialOption[];
}) {
  return (
    <section className="prompt-material-panel" aria-label="章节素材">
      <PromptPanelHeading
        title="章节"
        value={
          draft.recentChapterEnabled
            ? `最近 ${draft.recentChapterCount} 章 · ${draft.chapter_ids.length} 固定`
            : `${draft.chapter_ids.length} 固定`
        }
      />
      <div className="prompt-material-controls">
        <div className="prompt-recent-row">
          <label className="settings-check prompt-recent-toggle">
            <input
              checked={draft.recentChapterEnabled}
              onChange={(event) => onChangeDraft({ recentChapterEnabled: event.target.checked })}
              type="checkbox"
            />
            <span>最近 N 章</span>
          </label>
          <label className="settings-field prompt-recent-count">
            <input
              aria-label="最近章节章数"
              disabled={!draft.recentChapterEnabled}
              max={maxRecentChapterCount}
              min={0}
              onChange={(event) =>
                onChangeDraft({
                  recentChapterCount: normalizeRecentChapterCount(
                    Number.parseInt(event.target.value, 10),
                  ),
                })
              }
              placeholder="章数"
              type="number"
              value={draft.recentChapterCount}
            />
          </label>
        </div>
        <p className="prompt-material-note">最近章节会随当前章节移动；下方固定章节始终保留。</p>
      </div>
      <PromptCheckList
        emptyLabel="还没有章节。"
        onToggle={onToggleChapter}
        options={options}
        selectedIds={draft.chapter_ids}
      />
    </section>
  );
}

export function DocumentPromptMaterialPanel({
  draft,
  onToggleDocument,
  options,
}: {
  draft: PromptProfileDraft;
  onToggleDocument: (documentId: string) => void;
  options: PromptMaterialOption[];
}) {
  return (
    <section className="prompt-material-panel" aria-label="资料素材">
      <PromptPanelHeading title="资料" value={`${draft.document_ids.length} 已选`} />
      <PromptCheckList
        emptyLabel="还没有 Markdown 资料。"
        onToggle={onToggleDocument}
        options={options}
        selectedIds={draft.document_ids}
      />
    </section>
  );
}

function PromptPanelHeading({ title, value }: { title: string; value: string }) {
  return (
    <div className="prompt-panel-heading">
      <strong>{title}</strong>
      <span>{value}</span>
    </div>
  );
}

function PromptCheckList({
  emptyLabel,
  onToggle,
  options,
  selectedIds,
}: {
  emptyLabel: string;
  onToggle: (id: string) => void;
  options: PromptMaterialOption[];
  selectedIds: string[];
}) {
  return (
    <div className="prompt-check-list">
      {options.length ? (
        options.map((option) => (
          <label className="prompt-check-row" key={option.id}>
            <input
              checked={selectedIds.includes(option.id)}
              onChange={() => onToggle(option.id)}
              type="checkbox"
            />
            <span>{option.title}</span>
            <small>{option.meta}</small>
          </label>
        ))
      ) : (
        <p className="empty-note">{emptyLabel}</p>
      )}
    </div>
  );
}
