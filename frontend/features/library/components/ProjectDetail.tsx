import { BookMarked, CalendarClock, Download, FolderOpen, Pencil, Trash2 } from "lucide-react";

import type { ProjectInput, ProjectStatus, ProjectSummary } from "@/lib/api/index";
import { formatDate, statusLabels } from "@/features/library/utils";

export function ProjectDetail({
  editDraft,
  onChange,
  onDelete,
  onExport,
  onOpen,
  onSave,
  project,
}: {
  editDraft: Partial<ProjectInput>;
  onChange: (draft: Partial<ProjectInput>) => void;
  onDelete: () => void;
  onExport: () => void;
  onOpen: () => void;
  onSave: () => void;
  project?: ProjectSummary;
}) {
  if (!project) {
    return <p className="empty-note">还没有小说项目。</p>;
  }

  return (
    <>
      <div className="detail-heading">
        <div>
          <p className="eyebrow">{project.genre || "未分类"}</p>
          <h2>{project.title}</h2>
        </div>
        <div className="detail-heading-actions">
          <button
            className="secondary-button compact-action export-action"
            onClick={onExport}
            type="button"
          >
            <Download size={16} />
            导出
          </button>
          <button className="danger-button compact-action" onClick={onDelete} type="button">
            <Trash2 size={16} />
            删除
          </button>
          <button className="primary-icon-button compact-action" onClick={onOpen} type="button">
            <FolderOpen size={17} />
            打开
          </button>
        </div>
      </div>

      <div className="detail-meta">
        <span>
          <BookMarked size={15} />
          {statusLabels[project.status]}
        </span>
        <span>
          <CalendarClock size={15} />
          {formatDate(project.updated_at)}
        </span>
      </div>

      <textarea
        aria-label="项目简介"
        className="detail-description"
        onChange={(event) => onChange({ ...editDraft, description: event.target.value })}
        placeholder="简介 / 核心设定"
        value={editDraft.description ?? project.description}
      />

      <div className="form-grid">
        <input
          aria-label="书名"
          onChange={(event) => onChange({ ...editDraft, title: event.target.value })}
          placeholder="书名"
          value={editDraft.title ?? project.title}
        />
        <input
          aria-label="副标题"
          onChange={(event) => onChange({ ...editDraft, subtitle: event.target.value })}
          placeholder="副标题"
          value={editDraft.subtitle ?? project.subtitle}
        />
        <input
          aria-label="类型"
          onChange={(event) => onChange({ ...editDraft, genre: event.target.value })}
          placeholder="类型"
          value={editDraft.genre ?? project.genre}
        />
        <select
          aria-label="状态"
          onChange={(event) =>
            onChange({ ...editDraft, status: event.target.value as ProjectStatus })
          }
          value={editDraft.status ?? project.status}
        >
          {Object.entries(statusLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <button className="secondary-button" onClick={onSave} type="button">
        <Pencil size={16} />
        保存基本信息
      </button>
    </>
  );
}
