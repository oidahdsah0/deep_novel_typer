"use client";

import { useRef } from "react";
import type { PromptProfileDraft } from "../../types";

export function PromptTemplateEditor({
  activeTags,
  draft,
  onChangeDraft,
}: {
  activeTags: string[];
  draft: PromptProfileDraft;
  onChangeDraft: (patch: Partial<PromptProfileDraft>) => void;
}) {
  const systemRef = useRef<HTMLTextAreaElement | null>(null);
  const userRef = useRef<HTMLTextAreaElement | null>(null);

  function insertTag(target: "system" | "user", tag: string) {
    const ref = target === "system" ? systemRef : userRef;
    const field = target === "system" ? "system_template" : "user_template";
    const textarea = ref.current;
    const currentValue = draft[field];
    if (!textarea) {
      onChangeDraft({ [field]: `${currentValue}${tag}` } as Partial<PromptProfileDraft>);
      return;
    }
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const nextValue = `${currentValue.slice(0, start)}${tag}${currentValue.slice(end)}`;
    onChangeDraft({ [field]: nextValue } as Partial<PromptProfileDraft>);
    window.setTimeout(() => {
      textarea.focus();
      const caret = start + tag.length;
      textarea.setSelectionRange(caret, caret);
    }, 0);
  }

  return (
    <>
      <PromptTagBlock label="插入到系统提示词" onInsert={(tag) => insertTag("system", tag)} tags={activeTags} />
      <label className="settings-field">
        <span>System 提示词</span>
        <textarea
          ref={systemRef}
          onChange={(event) => onChangeDraft({ system_template: event.target.value })}
          value={draft.system_template}
        />
      </label>

      <PromptTagBlock label="插入到 User 提示词" onInsert={(tag) => insertTag("user", tag)} tags={activeTags} />
      <label className="settings-field">
        <span>User 提示词</span>
        <textarea
          ref={userRef}
          onChange={(event) => onChangeDraft({ user_template: event.target.value })}
          value={draft.user_template}
        />
      </label>
    </>
  );
}

function PromptTagBlock({
  label,
  onInsert,
  tags,
}: {
  label: string;
  onInsert: (tag: string) => void;
  tags: string[];
}) {
  return (
    <div className="prompt-tag-block">
      <span>{label}</span>
      <div className="prompt-tag-list">
        {tags.map((tag) => (
          <button key={`${label}-${tag}`} onClick={() => onInsert(tag)} type="button">
            {tag}
          </button>
        ))}
      </div>
    </div>
  );
}
