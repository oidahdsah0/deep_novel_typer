import { FilePlus2, X } from "lucide-react";

import type { ProjectInput, ProjectStatus } from "@/lib/api/index";
import { statusLabels } from "@/features/library/utils";

export function ProjectCreateDialog({
  draft,
  onChange,
  onClose,
  onCreate,
}: {
  draft: ProjectInput;
  onChange: (draft: ProjectInput) => void;
  onClose: () => void;
  onCreate: () => void;
}) {
  const canCreate = Boolean(draft.title.trim());

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        aria-label="新建小说"
        aria-modal="true"
        className="settings-dialog project-create-dialog"
        role="dialog"
      >
        <header className="settings-heading">
          <div>
            <p className="eyebrow">New Project</p>
            <h2>新建小说</h2>
          </div>
          <button aria-label="关闭" className="icon-button" onClick={onClose} type="button">
            <X size={18} />
          </button>
        </header>

        <input
          aria-label="新书名"
          onChange={(event) => onChange({ ...draft, title: event.target.value })}
          placeholder="书名"
          value={draft.title}
        />
        <input
          aria-label="新书副标题"
          onChange={(event) => onChange({ ...draft, subtitle: event.target.value })}
          placeholder="副标题"
          value={draft.subtitle}
        />
        <div className="form-grid">
          <input
            aria-label="新书类型"
            onChange={(event) => onChange({ ...draft, genre: event.target.value })}
            placeholder="类型"
            value={draft.genre}
          />
          <select
            aria-label="新书状态"
            onChange={(event) =>
              onChange({ ...draft, status: event.target.value as ProjectStatus })
            }
            value={draft.status}
          >
            {Object.entries(statusLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <textarea
          aria-label="新书简介"
          className="detail-description small"
          onChange={(event) => onChange({ ...draft, description: event.target.value })}
          placeholder="一句话核心设定"
          value={draft.description}
        />

        <div className="dialog-actions">
          <button className="secondary-button" onClick={onClose} type="button">
            取消
          </button>
          <button
            className="primary-button"
            disabled={!canCreate}
            onClick={onCreate}
            type="button"
          >
            <FilePlus2 size={17} />
            创建小说
          </button>
        </div>
      </section>
    </div>
  );
}
