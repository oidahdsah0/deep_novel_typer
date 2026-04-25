"use client";

import { Pencil, Plus, Trash2 } from "lucide-react";
import type { GenerationPreset, GenerationPresetKind } from "@/lib/api/index";

export function PresetEditor({
  kind,
  label,
  onAddPreset,
  onChangePreset,
  onChangePresetContent,
  onDeletePreset,
  onRenamePreset,
  placeholder,
  preset,
  presets,
  selectedPresetId,
}: {
  kind: GenerationPresetKind;
  label: string;
  onAddPreset: (kind: GenerationPresetKind) => void;
  onChangePreset: (presetId: string) => void;
  onChangePresetContent: (
    kind: GenerationPresetKind,
    preset: GenerationPreset,
    contentValue: string,
  ) => void;
  onDeletePreset: (preset: GenerationPreset) => void;
  onRenamePreset: (preset: GenerationPreset) => void;
  placeholder: string;
  preset: GenerationPreset | undefined;
  presets: GenerationPreset[];
  selectedPresetId: string;
}) {
  return (
    <section className="generation-section">
      <div className="generation-section-title">
        <span>{label}</span>
        {!preset ? (
          <small>无预设</small>
        ) : preset.is_system ? (
          <small>YAML 默认，可在本项目覆盖</small>
        ) : (
          <small>项目预设</small>
        )}
      </div>
      <div className="preset-toolbar">
        <select
          aria-label={label}
          className="preset-select"
          disabled={!presets.length}
          onChange={(event) => onChangePreset(event.target.value)}
          value={selectedPresetId}
        >
          {presets.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <button
          className="icon-button"
          onClick={() => onAddPreset(kind)}
          type="button"
          aria-label={`新增${label}`}
        >
          <Plus size={16} />
        </button>
        <button
          className="icon-button"
          disabled={!preset}
          onClick={() => preset && onRenamePreset(preset)}
          type="button"
          aria-label={`重命名${label}`}
        >
          <Pencil size={15} />
        </button>
        <button
          className="icon-button danger-icon"
          disabled={!preset}
          onClick={() => preset && onDeletePreset(preset)}
          type="button"
          aria-label={`删除${label}`}
        >
          <Trash2 size={15} />
        </button>
      </div>
      <textarea
        aria-label={`${label}提示词`}
        className="preset-editor"
        disabled={!preset}
        onChange={(event) =>
          preset && onChangePresetContent(kind, preset, event.target.value)
        }
        placeholder={placeholder}
        value={preset?.content ?? ""}
      />
    </section>
  );
}
