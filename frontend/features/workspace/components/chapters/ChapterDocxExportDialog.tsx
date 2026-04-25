"use client";

import { AlertCircle, Download, FileText, X } from "lucide-react";
import type { ChapterSummary } from "@/lib/api/index";

export function ChapterDocxExportDialog({
  chapters,
  error,
  isExporting,
  onClear,
  onClose,
  onExport,
  onSelectAll,
  onToggleChapter,
  selectedChapterIds,
}: {
  chapters: ChapterSummary[];
  error: string | null;
  isExporting: boolean;
  onClear: () => void;
  onClose: () => void;
  onExport: () => void;
  onSelectAll: () => void;
  onToggleChapter: (chapterId: string) => void;
  selectedChapterIds: string[];
}) {
  const selectedSet = new Set(selectedChapterIds);
  const selectedWordCount = chapters.reduce(
    (sum, chapter) => sum + (selectedSet.has(chapter.id) ? chapter.word_count : 0),
    0,
  );
  const canExport = selectedChapterIds.length > 0 && !isExporting;

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        aria-label="正文 DOCX 导出"
        className="settings-dialog chapter-docx-dialog"
        role="dialog"
      >
        <header className="settings-heading">
          <div>
            <p className="eyebrow">Chapter DOCX</p>
            <h2>正文 DOCX 导出</h2>
          </div>
          <button
            aria-label="关闭"
            className="icon-button"
            disabled={isExporting}
            onClick={onClose}
            type="button"
          >
            <X size={18} />
          </button>
        </header>

        <div className="chapter-docx-summary">
          <span>{selectedChapterIds.length} 个章节</span>
          <span>{selectedWordCount.toLocaleString("zh-CN")} 字</span>
        </div>

        <div className="chapter-docx-tools">
          <button
            className="secondary-button compact-action"
            disabled={isExporting || selectedChapterIds.length === chapters.length}
            onClick={onSelectAll}
            type="button"
          >
            全选
          </button>
          <button
            className="secondary-button compact-action"
            disabled={isExporting || selectedChapterIds.length === 0}
            onClick={onClear}
            type="button"
          >
            清空
          </button>
        </div>

        <div className="chapter-docx-list" aria-label="可导出的章节">
          {chapters.map((chapter) => {
            const selected = selectedSet.has(chapter.id);
            return (
              <label
                className={selected ? "chapter-docx-row selected" : "chapter-docx-row"}
                key={chapter.id}
              >
                <input
                  checked={selected}
                  disabled={isExporting}
                  onChange={() => onToggleChapter(chapter.id)}
                  type="checkbox"
                />
                <FileText size={15} />
                <span>
                  <strong>{chapter.title}</strong>
                  <small>{chapter.word_count.toLocaleString("zh-CN")} 字</small>
                </span>
              </label>
            );
          })}
        </div>

        {error ? (
          <div className="generation-error" role="alert">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        ) : null}

        <div className="dialog-actions">
          <button
            className="secondary-button"
            disabled={isExporting}
            onClick={onClose}
            type="button"
          >
            取消
          </button>
          <button
            className="primary-button"
            disabled={!canExport}
            onClick={onExport}
            type="button"
          >
            <Download size={16} />
            {isExporting ? "导出中" : "导出 DOCX"}
          </button>
        </div>
      </section>
    </div>
  );
}
