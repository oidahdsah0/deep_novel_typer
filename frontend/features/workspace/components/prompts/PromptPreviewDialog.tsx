"use client";

import { X } from "lucide-react";
import { useState } from "react";
import type { PromptPreviewResponse } from "@/lib/api/index";
import {
  messagesByRole,
  type PromptPreviewPanel,
  promptPreviewPanels,
} from "./promptPreviewUtils";
import { PromptPreviewContext } from "./PromptPreviewContext";
import { PromptPreviewMaterials } from "./PromptPreviewMaterials";
import { PromptPreviewSummary } from "./PromptPreviewSummary";
import { PromptPreviewTextBlock } from "./PromptPreviewTextBlock";
import { PromptPreviewWarnings } from "./PromptPreviewWarnings";

export function PromptPreviewDialog({
  onClose,
  preview,
}: {
  onClose: () => void;
  preview: PromptPreviewResponse;
}) {
  const [activeItemIndex, setActiveItemIndex] = useState(0);
  const [activePanel, setActivePanel] = useState<PromptPreviewPanel>("summary");
  const item = preview.items[activeItemIndex] ?? preview.items[0];
  const systemText = messagesByRole(item, "system");
  const userText = messagesByRole(item, "user");
  const warnings = [...(preview.warnings ?? []), ...(item?.warnings ?? [])];

  function copyText(value: string) {
    if (value) {
      void navigator.clipboard?.writeText(value);
    }
  }

  return (
    <div className="modal-backdrop generation-backdrop" role="presentation">
      <section
        aria-label="请求预览"
        className="settings-dialog prompt-preview-dialog"
        role="dialog"
      >
        <header className="settings-heading">
          <div>
            <p className="eyebrow">Request Dry Run</p>
            <h2>请求预览</h2>
          </div>
          <button className="icon-button" onClick={onClose} type="button" aria-label="关闭">
            <X size={18} />
          </button>
        </header>

        {preview.items.length > 1 ? (
          <div className="preview-item-tabs" aria-label="预览请求组">
            {preview.items.map((previewItem, index) => (
              <button
                className={activeItemIndex === index ? "active" : ""}
                key={`${previewItem.label}-${index}`}
                onClick={() => setActiveItemIndex(index)}
                type="button"
              >
                {previewItem.label}
              </button>
            ))}
          </div>
        ) : null}

        <div className="preview-panel-tabs" aria-label="预览内容">
          {promptPreviewPanels.map((panel) => (
            <button
              className={activePanel === panel.id ? "active" : ""}
              key={panel.id}
              onClick={() => setActivePanel(panel.id)}
              type="button"
            >
              {panel.label}
              {panel.id === "warnings" && warnings.length ? ` · ${warnings.length}` : ""}
            </button>
          ))}
        </div>

        <div className="preview-panel-body">
          {item && activePanel === "summary" ? (
            <PromptPreviewSummary item={item} preview={preview} />
          ) : null}
          {activePanel === "system" ? (
            <PromptPreviewTextBlock
              label="System Messages"
              onCopy={() => copyText(systemText)}
              value={systemText}
            />
          ) : null}
          {activePanel === "user" ? (
            <PromptPreviewTextBlock
              label="User Messages"
              onCopy={() => copyText(userText)}
              value={userText}
            />
          ) : null}
          {item && activePanel === "context" ? (
            <PromptPreviewContext contextPack={item.context_pack} onCopy={copyText} />
          ) : null}
          {item && activePanel === "materials" ? <PromptPreviewMaterials item={item} /> : null}
          {item && activePanel === "params" ? (
            <PromptPreviewTextBlock
              label="Request Options"
              onCopy={() => copyText(JSON.stringify(item.request_options, null, 2))}
              value={JSON.stringify(item.request_options, null, 2)}
            />
          ) : null}
          {activePanel === "warnings" ? <PromptPreviewWarnings warnings={warnings} /> : null}
        </div>
      </section>
    </div>
  );
}
