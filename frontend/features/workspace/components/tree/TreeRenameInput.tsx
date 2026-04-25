"use client";

import { Check, X } from "lucide-react";

export function TreeRenameInput({
  disabled,
  label,
  onCancel,
  onChange,
  onSubmit,
  title,
}: {
  disabled: boolean;
  label: string;
  onCancel: () => void;
  onChange: (title: string) => void;
  onSubmit: () => void;
  title: string;
}) {
  return (
    <form
      className="document-draft-form"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <input
        aria-label={label}
        autoFocus
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        placeholder="名称"
        value={title}
      />
      <button
        aria-label={`确认${label}`}
        className="tiny-tool"
        disabled={disabled || !title.trim()}
        type="submit"
      >
        <Check size={13} />
      </button>
      <button
        aria-label="取消"
        className="tiny-tool"
        disabled={disabled}
        onClick={onCancel}
        type="button"
      >
        <X size={13} />
      </button>
    </form>
  );
}
