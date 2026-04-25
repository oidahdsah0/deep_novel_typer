"use client";

import { RotateCcw, Save, X } from "lucide-react";
import type { ResourceVersion, ResourceVersionDetail } from "@/lib/api/index";
import { formatDateTime, versionTypeLabel } from "../../utils";

export function VersionDialog({
  draft,
  isLoading,
  onChangeDraft,
  onClose,
  onCreateManual,
  onRestore,
  onSelectVersion,
  resourceTitle,
  selectedVersion,
  versions,
}: {
  draft: { label: string; note: string };
  isLoading: boolean;
  onChangeDraft: (draft: { label: string; note: string }) => void;
  onClose: () => void;
  onCreateManual: () => void;
  onRestore: (version: ResourceVersionDetail) => void;
  onSelectVersion: (version: ResourceVersion) => void;
  resourceTitle: string;
  selectedVersion: ResourceVersionDetail | null;
  versions: ResourceVersion[];
}) {
  return (
    <div className="modal-backdrop generation-backdrop" role="presentation">
      <section
        aria-label="历史版本"
        className="settings-dialog version-dialog"
        role="dialog"
      >
        <div className="settings-heading">
          <div>
            <p className="eyebrow">Version History</p>
            <h2>{resourceTitle}</h2>
          </div>
          <button className="icon-button" onClick={onClose} type="button" aria-label="关闭">
            <X size={17} />
          </button>
        </div>

        <section className="version-create">
          <label className="settings-field">
            <span>版本名</span>
            <input
              onChange={(event) => onChangeDraft({ ...draft, label: event.target.value })}
              placeholder="例如：第一幕定稿"
              value={draft.label}
            />
          </label>
          <label className="settings-field">
            <span>备注</span>
            <input
              onChange={(event) => onChangeDraft({ ...draft, note: event.target.value })}
              placeholder="这次改动的原因"
              value={draft.note}
            />
          </label>
          <button
            className="primary-button"
            disabled={isLoading}
            onClick={onCreateManual}
            type="button"
          >
            <Save size={16} />
            保存当前版本
          </button>
        </section>

        <div className="version-manager">
          <div className="version-list" aria-label="历史版本列表">
            {versions.length ? (
              versions.map((version) => (
                <button
                  className={
                    selectedVersion?.id === version.id
                      ? "version-list-item active"
                      : "version-list-item"
                  }
                  key={version.id}
                  onClick={() => onSelectVersion(version)}
                  type="button"
                >
                  <span>{version.label || versionTypeLabel(version.version_type)}</span>
                  <small>
                    {formatDateTime(version.created_at)} · {version.word_count} 字
                  </small>
                </button>
              ))
            ) : (
              <p className="empty-note">还没有历史版本。</p>
            )}
          </div>

          <div className="version-preview" aria-label="历史版本预览">
            {selectedVersion ? (
              <>
                <div className="version-preview-heading">
                  <div>
                    <strong>{selectedVersion.label || versionTypeLabel(selectedVersion.version_type)}</strong>
                    <span>{formatDateTime(selectedVersion.created_at)}</span>
                  </div>
                  <button
                    className="secondary-button"
                    disabled={isLoading}
                    onClick={() => onRestore(selectedVersion)}
                    type="button"
                  >
                    <RotateCcw size={15} />
                    恢复
                  </button>
                </div>
                {selectedVersion.note ? <p>{selectedVersion.note}</p> : null}
                <pre>{selectedVersion.content}</pre>
              </>
            ) : (
              <p className="empty-note">选择一个版本查看内容。</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
