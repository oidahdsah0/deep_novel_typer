"use client";

import { AlertCircle, Check, LoaderCircle, X } from "lucide-react";
import { draftActionLabels, sourceLabels } from "../../constants";
import type { PendingDraftGenerationState } from "../../types";

export function PendingDraftConfirmation({
  onAccept,
  onReject,
  pending,
}: {
  onAccept: () => void;
  onReject: () => void;
  pending: PendingDraftGenerationState;
}) {
  if (pending.status === "generating") {
    return (
      <div className="pending-draft-confirmation generating" role="status">
        <LoaderCircle aria-hidden className="pending-draft-spinner" size={16} />
        <div>
          <span className="pending-draft-label">生成中</span>
          <span className="pending-draft-detail">{draftActionLabels[pending.action]}</span>
        </div>
      </div>
    );
  }

  if (pending.status === "error") {
    return (
      <div className="pending-draft-confirmation error" role="alert">
        <AlertCircle aria-hidden size={16} />
        <div>
          <span className="pending-draft-label">生成失败</span>
          <span className="pending-draft-detail">{pending.error}</span>
        </div>
        <button
          aria-label="关闭生成失败提示"
          className="pending-draft-action reject"
          onClick={onReject}
          title="关闭"
          type="button"
        >
          <X size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="pending-draft-confirmation ready" role="group" aria-label="待确认生成内容">
      <div>
        <span className="pending-draft-label">待确认</span>
        <span className="pending-draft-detail">
          {sourceLabels[pending.source]} · {pending.model ?? "本地兜底"}
        </span>
      </div>
      <div className="pending-draft-actions">
        <button
          aria-label="废弃生成内容"
          className="pending-draft-action reject"
          onClick={onReject}
          title="废弃"
          type="button"
        >
          <X size={16} />
        </button>
        <button
          aria-label="采纳生成内容"
          className="pending-draft-action accept"
          onClick={onAccept}
          title="采纳"
          type="button"
        >
          <Check size={16} />
        </button>
      </div>
    </div>
  );
}
