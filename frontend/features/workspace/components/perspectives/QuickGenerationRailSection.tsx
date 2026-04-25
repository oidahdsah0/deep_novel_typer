"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import type {
  ApiConfig,
  GenerationPreset,
  GenerationPresetKind,
  PromptProfile,
} from "@/lib/api/index";
import type { PresetSaveState } from "../../types";
import { QuickGenerationSettingsPanel } from "./QuickGenerationSettingsPanel";

export function QuickGenerationRailSection({
  authorPreset,
  authorPresets,
  isCollapsed,
  llmConfigs,
  onAddGenerationPreset,
  onChangeAuthorPreset,
  onChangePresetContent,
  onDeleteGenerationPreset,
  onRenameGenerationPreset,
  onSaveQuickGenerationProfile,
  onToggleCollapsed,
  presetSaveState,
  promptProfiles,
  quickGenerationProfileSaveState,
  selectedAuthorPresetId,
}: QuickGenerationRailSectionProps) {
  return (
    <section className="quick-generation-rail-section" aria-label="快速生成设置">
      <header
        className={
          isCollapsed
            ? "quick-generation-section-heading rail-collapsible-heading collapsed"
            : "quick-generation-section-heading rail-collapsible-heading"
        }
      >
        <button
          aria-expanded={!isCollapsed}
          className="rail-section-toggle"
          onClick={onToggleCollapsed}
          type="button"
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
          <span className="rail-section-toggle-copy">
            <span className="eyebrow">Quick Generate</span>
            <span className="rail-section-title">快速生成设置</span>
          </span>
        </button>
      </header>
      {isCollapsed ? null : (
        <QuickGenerationSettingsPanel
          authorPreset={authorPreset}
          authorPresets={authorPresets}
          llmConfigs={llmConfigs}
          onAddPreset={onAddGenerationPreset}
          onChangeAuthorPreset={onChangeAuthorPreset}
          onChangePresetContent={onChangePresetContent}
          onDeletePreset={onDeleteGenerationPreset}
          onRenamePreset={onRenameGenerationPreset}
          onSaveProfile={onSaveQuickGenerationProfile}
          presetSaveState={presetSaveState}
          profileSaveState={quickGenerationProfileSaveState}
          promptProfiles={promptProfiles}
          selectedAuthorPresetId={selectedAuthorPresetId}
        />
      )}
    </section>
  );
}

type QuickGenerationRailSectionProps = {
  authorPreset: GenerationPreset | undefined;
  authorPresets: GenerationPreset[];
  isCollapsed: boolean;
  llmConfigs: ApiConfig[];
  onAddGenerationPreset: (kind: GenerationPresetKind) => Promise<void>;
  onChangeAuthorPreset: (presetId: string) => void;
  onChangePresetContent: (
    kind: GenerationPresetKind,
    preset: GenerationPreset,
    contentValue: string,
  ) => void;
  onDeleteGenerationPreset: (preset: GenerationPreset) => Promise<void>;
  onRenameGenerationPreset: (preset: GenerationPreset) => Promise<void>;
  onSaveQuickGenerationProfile: (patch: {
    apiConfigId?: string;
    includeChapterSynopsis?: boolean;
    systemTemplate?: string;
    temperature?: string;
    userTemplate?: string;
  }) => Promise<void>;
  onToggleCollapsed: () => void;
  presetSaveState: PresetSaveState;
  promptProfiles: PromptProfile[];
  quickGenerationProfileSaveState: PresetSaveState;
  selectedAuthorPresetId: string;
};
