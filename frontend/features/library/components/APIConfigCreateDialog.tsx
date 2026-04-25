import { FilePlus2, X } from "lucide-react";

import type { ApiConfigInput, ApiConfigTemplate } from "@/lib/api/index";
import { APIConfigFields } from "@/features/library/components/APIConfigFields";

export function APIConfigCreateDialog({
  draft,
  onChange,
  onClose,
  onCreate,
  templates,
}: {
  draft: ApiConfigInput;
  onChange: (draft: ApiConfigInput) => void;
  onClose: () => void;
  onCreate: () => void;
  templates: ApiConfigTemplate[];
}) {
  const canCreate = Boolean(
    draft.name.trim() && draft.base_url.trim() && draft.model.trim(),
  );

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        aria-label="新建 API 配置"
        aria-modal="true"
        className="settings-dialog api-config-create-dialog"
        role="dialog"
      >
        <header className="settings-heading">
          <div>
            <p className="eyebrow">New API</p>
            <h2>新建配置</h2>
          </div>
          <button
            aria-label="关闭"
            className="icon-button"
            onClick={onClose}
            type="button"
          >
            <X size={18} />
          </button>
        </header>

        <APIConfigFields
          draft={draft}
          keyConfigured={false}
          onChange={onChange}
          templates={templates}
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
            创建配置
          </button>
        </div>
      </section>
    </div>
  );
}
