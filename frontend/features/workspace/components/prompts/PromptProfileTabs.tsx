"use client";

import type { PromptRequestType } from "@/lib/api/index";
import { promptRequestLabels, promptRequestTypes } from "../../constants";

export function PromptProfileTabs({
  activeRequestType,
  onSelectRequestType,
}: {
  activeRequestType: PromptRequestType;
  onSelectRequestType: (requestType: PromptRequestType) => void;
}) {
  return (
    <div className="prompt-tabs" aria-label="请求类型">
      {promptRequestTypes.map((requestType) => (
        <button
          className={activeRequestType === requestType ? "active" : ""}
          key={requestType}
          onClick={() => onSelectRequestType(requestType)}
          type="button"
        >
          {promptRequestLabels[requestType]}
        </button>
      ))}
    </div>
  );
}
