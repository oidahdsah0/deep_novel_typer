"use client";

import type { FormEvent, RefObject } from "react";
import type {
  ConfirmRequest,
  DialogRequest,
  NoticeRequest,
  PromptRequest,
} from "./dialogTypes";

type DialogViewProps = {
  active: DialogRequest | null;
  confirmButtonRef: RefObject<HTMLButtonElement | null>;
  dialogRef: RefObject<HTMLDivElement | null>;
  noticeButtonRef: RefObject<HTMLButtonElement | null>;
  onConfirm: (request: ConfirmRequest, value: boolean) => void;
  onNotice: (request: NoticeRequest) => void;
  onPromptCancel: (request: PromptRequest) => void;
  onPromptChange: (value: string) => void;
  onPromptSubmit: (request: PromptRequest) => void;
  promptInputRef: RefObject<HTMLInputElement | null>;
  promptValue: string;
};

export function DialogView({
  active,
  confirmButtonRef,
  dialogRef,
  noticeButtonRef,
  onConfirm,
  onNotice,
  onPromptCancel,
  onPromptChange,
  onPromptSubmit,
  promptInputRef,
  promptValue,
}: DialogViewProps) {
  if (!active) return null;

  return (
    <div className="modal-backdrop app-dialog-backdrop" ref={dialogRef} role="presentation">
      {active.kind === "confirm" ? (
        <section
          aria-label={active.options.title ?? "确认操作"}
          aria-modal="true"
          className="settings-dialog app-dialog"
          role="dialog"
        >
          <DialogHeader title={active.options.title ?? "确认操作"} />
          <p className="app-dialog-message">{active.message}</p>
          <div className="dialog-actions app-dialog-actions">
            <button
              className="secondary-button"
              onClick={() => onConfirm(active, false)}
              type="button"
            >
              {active.options.cancelLabel ?? "取消"}
            </button>
            <button
              className={active.options.tone === "danger" ? "danger-button" : "primary-button"}
              onClick={() => onConfirm(active, true)}
              ref={confirmButtonRef}
              type="button"
            >
              {active.options.confirmLabel ?? "确认"}
            </button>
          </div>
        </section>
      ) : active.kind === "prompt" ? (
        <PromptDialog
          promptInputRef={promptInputRef}
          promptValue={promptValue}
          request={active}
          onPromptCancel={onPromptCancel}
          onPromptChange={onPromptChange}
          onPromptSubmit={onPromptSubmit}
        />
      ) : (
        <section
          aria-label={active.options.title ?? "提示"}
          aria-modal="true"
          className="settings-dialog app-dialog"
          role="dialog"
        >
          <DialogHeader title={active.options.title ?? "提示"} />
          <p className="app-dialog-message">{active.message}</p>
          <div className="dialog-actions app-dialog-actions">
            <button
              className="primary-button"
              onClick={() => onNotice(active)}
              ref={noticeButtonRef}
              type="button"
            >
              {active.options.closeLabel ?? "知道了"}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}

function PromptDialog({
  onPromptCancel,
  onPromptChange,
  onPromptSubmit,
  promptInputRef,
  promptValue,
  request,
}: {
  onPromptCancel: (request: PromptRequest) => void;
  onPromptChange: (value: string) => void;
  onPromptSubmit: (request: PromptRequest) => void;
  promptInputRef: RefObject<HTMLInputElement | null>;
  promptValue: string;
  request: PromptRequest;
}) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onPromptSubmit(request);
  }

  return (
    <section
      aria-label={request.options.title ?? "输入内容"}
      aria-modal="true"
      className="settings-dialog app-dialog"
      role="dialog"
    >
      <DialogHeader title={request.options.title ?? "输入内容"} />
      <form className="app-dialog-form" onSubmit={handleSubmit}>
        <label className="settings-field">
          <span>{request.message}</span>
          <input
            onChange={(event) => onPromptChange(event.target.value)}
            placeholder={request.options.placeholder}
            ref={promptInputRef}
            value={promptValue}
          />
        </label>
        <div className="dialog-actions app-dialog-actions">
          <button
            className="secondary-button"
            onClick={() => onPromptCancel(request)}
            type="button"
          >
            {request.options.cancelLabel ?? "取消"}
          </button>
          <button className="primary-button" type="submit">
            {request.options.confirmLabel ?? "确认"}
          </button>
        </div>
      </form>
    </section>
  );
}

function DialogHeader({ title }: { title: string }) {
  return (
    <header className="settings-heading">
      <div>
        <h2>{title}</h2>
      </div>
    </header>
  );
}
