"use client";

import { Pilcrow, RotateCcw, Save, X } from "lucide-react";
import type { CSSProperties } from "react";
import type { TypewriterLayoutToolboxApi } from "@/features/workspace/hooks/useTypewriterLayoutToolbox";
import { useDraggableToolbox } from "@/features/workspace/hooks/useDraggableToolbox";

type TypewriterLayoutToolboxProps = {
  toolbox: TypewriterLayoutToolboxApi;
};

export function TypewriterLayoutToolbox({ toolbox }: TypewriterLayoutToolboxProps) {
  const { dragHandlers, drawerRef, drawerStyle, isDragging } = useDraggableToolbox(toolbox.isOpen);

  if (!toolbox.isOpen) return null;

  const previewFontSizePx = Math.round(toolbox.draftSettings.font_size_px * 7.5) / 10;
  const previewLineHeightPx =
    Math.round(toolbox.draftSettings.line_height_multiplier * previewFontSizePx * 10) / 10;

  return (
    <aside
      aria-label="排版工具箱"
      className={`typewriter-toolbox-drawer${isDragging ? " is-dragging" : ""}`}
      ref={drawerRef}
      style={drawerStyle}
    >
      <header className="typewriter-toolbox-header" {...dragHandlers}>
        <div>
          <p className="eyebrow">Typewriter Layout</p>
          <h2>排版工具箱</h2>
        </div>
        <button
          aria-label="关闭排版工具箱"
          className="icon-button"
          onClick={() => toolbox.setIsOpen(false)}
          type="button"
        >
          <X size={17} />
        </button>
      </header>
      <div className="typewriter-toolbox-body">
        {toolbox.error ? <p className="typewriter-message error">{toolbox.error}</p> : null}
        {toolbox.notice ? <p className="typewriter-message">{toolbox.notice}</p> : null}
        <div className="typewriter-control-grid">
          <NumberField
            label="段首缩进"
            max={8}
            min={0}
            suffix="字符"
            value={toolbox.draftSettings.first_line_indent_chars}
            onChange={(first_line_indent_chars) =>
              toolbox.setDraftSettings((current) => ({
                ...current,
                first_line_indent_chars,
              }))
            }
          />
          <NumberField
            label="段落距离"
            max={5}
            min={0}
            suffix="空行"
            value={toolbox.draftSettings.paragraph_gap_lines}
            onChange={(paragraph_gap_lines) =>
              toolbox.setDraftSettings((current) => ({
                ...current,
                paragraph_gap_lines,
              }))
            }
          />
          <NumberField
            label="行距"
            max={4}
            min={1}
            suffix="倍"
            value={toolbox.draftSettings.line_height_multiplier}
            onChange={(line_height_multiplier) =>
              toolbox.setDraftSettings((current) => ({
                ...current,
                line_height_multiplier,
              }))
            }
          />
          <NumberField
            label="字号"
            max={32}
            min={12}
            step={1}
            suffix="px"
            value={toolbox.draftSettings.font_size_px}
            onChange={(font_size_px) =>
              toolbox.setDraftSettings((current) => ({
                ...current,
                font_size_px,
              }))
            }
          />
        </div>
        <div className="typewriter-preview" aria-label="版式预览">
          <Pilcrow size={16} />
          <div
            style={{
              "--typewriter-first-line-indent-chars":
                toolbox.draftSettings.first_line_indent_chars,
              "--typewriter-line-height-multiplier":
                toolbox.draftSettings.line_height_multiplier,
              "--typewriter-preview-font-size-px": `${previewFontSizePx}px`,
              "--typewriter-preview-line-height-px": `${previewLineHeightPx}px`,
              "--typewriter-paragraph-gap-lines":
                toolbox.draftSettings.paragraph_gap_lines,
            } as CSSProperties}
          >
            <p>雾从旧码头升上来，灯塔的光像迟疑的笔锋。</p>
            <p>林澈把录音笔放进口袋，听见潮声里有另一串脚步。</p>
          </div>
        </div>
        <div className="typewriter-toolbox-actions">
          <button
            className="secondary-button"
            disabled={toolbox.isSaving}
            onClick={toolbox.resetDraftToDefault}
            type="button"
          >
            <RotateCcw size={15} />
            恢复默认
          </button>
          <button
            className="primary-button"
            disabled={toolbox.isSaving || !toolbox.hasUnsavedSettings}
            onClick={() => void toolbox.saveSettings()}
            type="button"
          >
            <Save size={15} />
            {toolbox.isSaving ? "保存中" : "保存"}
          </button>
        </div>
      </div>
    </aside>
  );
}

function NumberField({
  label,
  max,
  min,
  onChange,
  step = 0.1,
  suffix,
  value,
}: {
  label: string;
  max: number;
  min: number;
  onChange: (value: number) => void;
  step?: number;
  suffix: string;
  value: number;
}) {
  return (
    <label className="typewriter-number-field">
      <span>{label}</span>
      <div>
        <input
          max={max}
          min={min}
          onChange={(event) => onChange(clampInput(event.target.value, min, max, step))}
          step={step}
          type="number"
          value={value}
        />
        <small>{suffix}</small>
      </div>
    </label>
  );
}

function clampInput(value: string, min: number, max: number, step: number) {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) return min;
  const snapped = Math.round(parsed / step) * step;
  const rounded = step >= 1 ? Math.round(snapped) : Math.round(snapped * 10) / 10;
  return Math.min(max, Math.max(min, rounded));
}
