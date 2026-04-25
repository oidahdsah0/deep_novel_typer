"use client";

import { Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";
import type { EmbeddingTag, EmbeddingTagInput, EmbeddingTagUpdate } from "@/lib/api/index";

const defaultColor = "#d94841";

type EmbeddingTagManagerProps = {
  isSaving: boolean;
  onCreate: (input: EmbeddingTagInput) => Promise<void>;
  onDelete: (tag: EmbeddingTag) => Promise<void>;
  onUpdate: (tagId: string, input: EmbeddingTagUpdate) => Promise<void>;
  tags: EmbeddingTag[];
};

export function EmbeddingTagManager({
  isSaving,
  onCreate,
  onDelete,
  onUpdate,
  tags,
}: EmbeddingTagManagerProps) {
  const [draft, setDraft] = useState<EmbeddingTagInput>({
    name: "",
    description: "",
    color: defaultColor,
    is_enabled: true,
  });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<EmbeddingTagInput | null>(null);

  async function submitNewTag() {
    if (!draft.name.trim()) return;
    await onCreate({
      name: draft.name.trim(),
      description: draft.description?.trim() ?? "",
      color: draft.color || defaultColor,
      is_enabled: draft.is_enabled ?? true,
    });
    setDraft({ name: "", description: "", color: defaultColor, is_enabled: true });
  }

  function startEdit(tag: EmbeddingTag) {
    setEditingId(tag.id);
    setEditDraft({
      name: tag.name,
      description: tag.description,
      color: tag.color,
      is_enabled: tag.is_enabled,
    });
  }

  async function submitEdit(tagId: string) {
    if (!editDraft?.name.trim()) return;
    await onUpdate(tagId, {
      name: editDraft.name.trim(),
      description: editDraft.description?.trim() ?? "",
      color: editDraft.color || defaultColor,
      is_enabled: editDraft.is_enabled ?? true,
    });
    setEditingId(null);
    setEditDraft(null);
  }

  return (
    <div className="embedding-panel-stack">
      <section className="embedding-tag-form">
        <div className="embedding-tag-form-main">
          <input
            onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))}
            placeholder="标签名"
            value={draft.name}
          />
          <input
            aria-label="标签颜色"
            onChange={(event) => setDraft((current) => ({ ...current, color: event.target.value }))}
            type="color"
            value={draft.color ?? defaultColor}
          />
        </div>
        <textarea
          onChange={(event) =>
            setDraft((current) => ({ ...current, description: event.target.value }))
          }
          placeholder="描述"
          rows={3}
          value={draft.description}
        />
        <div className="embedding-tag-form-row">
          <label className="embedding-switch-row">
            <input
              checked={draft.is_enabled ?? true}
              onChange={(event) =>
                setDraft((current) => ({ ...current, is_enabled: event.target.checked }))
              }
              type="checkbox"
            />
            <span />
            <strong>启用</strong>
          </label>
          <button
            className="icon-button"
            disabled={isSaving || !draft.name.trim()}
            onClick={() => void submitNewTag()}
            type="button"
            aria-label="新增标签"
          >
            <Plus size={16} />
          </button>
        </div>
      </section>

      <div className="embedding-tag-list">
        {tags.map((tag) =>
          editingId === tag.id && editDraft ? (
            <article className="embedding-tag-card editing" key={tag.id}>
              <div className="embedding-tag-form-main">
                <input
                  onChange={(event) =>
                    setEditDraft((current) => ({ ...requireDraft(current), name: event.target.value }))
                  }
                  value={editDraft.name}
                />
                <input
                  aria-label="标签颜色"
                  onChange={(event) =>
                    setEditDraft((current) => ({ ...requireDraft(current), color: event.target.value }))
                  }
                  type="color"
                  value={editDraft.color ?? defaultColor}
                />
              </div>
              <textarea
                onChange={(event) =>
                  setEditDraft((current) => ({
                    ...requireDraft(current),
                    description: event.target.value,
                  }))
                }
                rows={3}
                value={editDraft.description}
              />
              <div className="embedding-tag-actions">
                <label className="embedding-switch-row">
                  <input
                    checked={editDraft.is_enabled ?? true}
                    onChange={(event) =>
                      setEditDraft((current) => ({
                        ...requireDraft(current),
                        is_enabled: event.target.checked,
                      }))
                    }
                    type="checkbox"
                  />
                  <span />
                  <strong>启用</strong>
                </label>
                <button
                  aria-label="保存标签"
                  className="icon-button"
                  disabled={isSaving}
                  onClick={() => void submitEdit(tag.id)}
                  type="button"
                >
                  <Check size={16} />
                </button>
                <button
                  aria-label="取消编辑"
                  className="icon-button"
                  onClick={() => {
                    setEditingId(null);
                    setEditDraft(null);
                  }}
                  type="button"
                >
                  <X size={16} />
                </button>
              </div>
            </article>
          ) : (
            <article className="embedding-tag-card" key={tag.id}>
              <div className="embedding-tag-card-head">
                <i style={{ backgroundColor: tag.color }} />
                <div>
                  <strong>{tag.name}</strong>
                  {tag.description ? <p>{tag.description}</p> : null}
                </div>
                <span>{tag.is_enabled ? "启用" : "停用"}</span>
              </div>
              <div className="embedding-tag-actions">
                <button
                  aria-label="编辑标签"
                  className="icon-button"
                  disabled={isSaving}
                  onClick={() => startEdit(tag)}
                  type="button"
                >
                  <Pencil size={15} />
                </button>
                <button
                  aria-label="删除标签"
                  className="icon-button danger-tool"
                  disabled={isSaving}
                  onClick={() => void onDelete(tag)}
                  type="button"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </article>
          ),
        )}
      </div>
    </div>
  );
}

function requireDraft(value: EmbeddingTagInput | null): EmbeddingTagInput {
  return value ?? { name: "", description: "", color: defaultColor, is_enabled: true };
}
