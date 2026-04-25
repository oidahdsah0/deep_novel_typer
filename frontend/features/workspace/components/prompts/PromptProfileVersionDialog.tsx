"use client";

import { Copy, RotateCcw, X } from "lucide-react";
import type { PromptProfileVersion, PromptProfileVersionDetail, PromptRequestType } from "@/lib/api/index";
import { promptRequestLabels } from "../../constants";
import { formatDateTime, promptProfileVersionTypeLabel } from "../../utils";

export function PromptProfileVersionDialog({
  isLoading,
  onClose,
  onRestore,
  onSelectVersion,
  requestType,
  selectedVersion,
  versions,
}: {
  isLoading: boolean;
  onClose: () => void;
  onRestore: (version: PromptProfileVersionDetail) => void;
  onSelectVersion: (version: PromptProfileVersion) => void;
  requestType: PromptRequestType;
  selectedVersion: PromptProfileVersionDetail | null;
  versions: PromptProfileVersion[];
}) {
  const snapshot = selectedVersion?.snapshot;
  const configText = snapshot ? JSON.stringify(snapshot.config, null, 2) : "";

  function copyText(value: string) {
    if (!value) {
      return;
    }
    void navigator.clipboard?.writeText(value);
  }

  return (
    <div className="modal-backdrop generation-backdrop" role="presentation">
      <section
        aria-label="请求配置历史"
        className="settings-dialog prompt-version-dialog"
        role="dialog"
      >
        <div className="settings-heading">
          <div>
            <p className="eyebrow">Request History</p>
            <h2>{promptRequestLabels[requestType]}</h2>
          </div>
          <button className="icon-button" onClick={onClose} type="button" aria-label="关闭">
            <X size={17} />
          </button>
        </div>

        <div className="version-manager prompt-version-manager">
          <div className="version-list" aria-label="请求配置历史列表">
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
                  <span>{version.label || promptProfileVersionTypeLabel(version.version_type)}</span>
                  <small>
                    {formatDateTime(version.created_at)} · System {version.system_chars} 字 · User{" "}
                    {version.user_chars} 字
                  </small>
                  <small>
                    {version.chapter_count} 章 · {version.document_count} 资料 ·{" "}
                    {promptProfileVersionTypeLabel(version.version_type)}
                  </small>
                </button>
              ))
            ) : (
              <p className="empty-note">还没有请求配置历史。保存一次后会自动生成初始配置和手动保存版本。</p>
            )}
          </div>

          <div className="version-preview prompt-version-preview" aria-label="请求配置历史预览">
            {selectedVersion && snapshot ? (
              <>
                <div className="version-preview-heading">
                  <div>
                    <strong>
                      {selectedVersion.label ||
                        promptProfileVersionTypeLabel(selectedVersion.version_type)}
                    </strong>
                    <span>
                      {formatDateTime(selectedVersion.created_at)} ·{" "}
                      {promptProfileVersionTypeLabel(selectedVersion.version_type)}
                    </span>
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
                <section className="prompt-version-meta">
                  <div>
                    <span>固定章节</span>
                    <strong>{snapshot.chapter_ids.length}</strong>
                  </div>
                  <div>
                    <span>资料</span>
                    <strong>{snapshot.document_ids.length}</strong>
                  </div>
                  <div>
                    <span>配置键</span>
                    <strong>{Object.keys(snapshot.config).length}</strong>
                  </div>
                </section>
                <section className="prompt-version-fields">
                  <div className="preview-block-heading">
                    <span>System 提示词</span>
                    <button
                      className="secondary-button compact-action"
                      onClick={() => copyText(snapshot.system_template)}
                      type="button"
                    >
                      <Copy size={14} />
                      复制
                    </button>
                  </div>
                  <textarea readOnly value={snapshot.system_template} />
                  <div className="preview-block-heading">
                    <span>User 提示词</span>
                    <button
                      className="secondary-button compact-action"
                      onClick={() => copyText(snapshot.user_template)}
                      type="button"
                    >
                      <Copy size={14} />
                      复制
                    </button>
                  </div>
                  <textarea readOnly value={snapshot.user_template} />
                  <div className="preview-block-heading">
                    <span>请求配置 JSON</span>
                    <button
                      className="secondary-button compact-action"
                      onClick={() => copyText(configText)}
                      type="button"
                    >
                      <Copy size={14} />
                      复制
                    </button>
                  </div>
                  <textarea readOnly value={configText} />
                </section>
              </>
            ) : (
              <p className="empty-note">选择一个历史版本查看完整请求配置。</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
