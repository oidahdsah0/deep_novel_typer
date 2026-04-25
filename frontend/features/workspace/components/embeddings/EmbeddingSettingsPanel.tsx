"use client";

import { RefreshCw } from "lucide-react";
import type {
  ApiConfig,
  EmbeddingDistanceAlgorithm,
  EmbeddingSegmentationMode,
} from "@/lib/api/index";

type EmbeddingSettingsPanelProps = {
  algorithm: EmbeddingDistanceAlgorithm;
  embeddingConfigs: ApiConfig[];
  hasUnsavedSettings: boolean;
  isLoading: boolean;
  isSaving: boolean;
  onAlgorithmChange: (value: EmbeddingDistanceAlgorithm) => void;
  onConfigChange: (value: string) => void;
  onRegenerateVectors: () => void;
  onSegmentationChange: (value: EmbeddingSegmentationMode) => void;
  onSegmentSizeChange: (value: number) => void;
  segmentationMode: EmbeddingSegmentationMode;
  segmentSize: number;
  selectedApiConfigId: string;
};

export function EmbeddingSettingsPanel({
  algorithm,
  embeddingConfigs,
  hasUnsavedSettings,
  isLoading,
  isSaving,
  onAlgorithmChange,
  onConfigChange,
  onRegenerateVectors,
  onSegmentationChange,
  onSegmentSizeChange,
  segmentationMode,
  segmentSize,
  selectedApiConfigId,
}: EmbeddingSettingsPanelProps) {
  const selectedConfig = embeddingConfigs.find((config) => config.id === selectedApiConfigId);
  const segmentUnit = segmentationMode === "word" ? "词" : "句";

  return (
    <div className="embedding-panel-stack">
      <label className="embedding-field">
        <span>Embedding 配置</span>
        <select value={selectedApiConfigId} onChange={(event) => onConfigChange(event.target.value)}>
          {embeddingConfigs.length === 0 ? <option value="">无可用配置</option> : null}
          {embeddingConfigs.map((config) => (
            <option key={config.id} value={config.id}>
              {config.name}
            </option>
          ))}
        </select>
      </label>

      {selectedConfig ? (
        <div className="embedding-config-summary">
          <span>{selectedConfig.provider}</span>
          <strong>{selectedConfig.model}</strong>
          <span>{selectedConfig.dimensions ? `${selectedConfig.dimensions} 维` : "自动维度"}</span>
        </div>
      ) : null}

      <div className="embedding-field-grid">
        <label className="embedding-field">
          <span>切片</span>
          <select
            value={segmentationMode}
            onChange={(event) => onSegmentationChange(event.target.value as EmbeddingSegmentationMode)}
          >
            <option value="word">分词</option>
            <option value="sentence">句子</option>
          </select>
        </label>
        <label className="embedding-field">
          <span>片段长度（每片 {segmentSize} {segmentUnit}）</span>
          <input
            max={12}
            min={1}
            onChange={(event) => onSegmentSizeChange(clampSegmentSize(event.target.value))}
            type="number"
            value={segmentSize}
          />
        </label>
        <label className="embedding-field">
          <span>距离</span>
          <select
            value={algorithm}
            onChange={(event) => onAlgorithmChange(event.target.value as EmbeddingDistanceAlgorithm)}
          >
            <option value="cosine">Cosine</option>
            <option value="euclidean">Euclidean</option>
            <option value="manhattan">Manhattan</option>
          </select>
        </label>
      </div>

      <div className="embedding-settings-action">
        <div>
          <span>向量更新</span>
          <p>
            {hasUnsavedSettings
              ? "设置尚未保存。点击按钮后保存当前设置，并重新生成已有分析结果。"
              : "当前设置已保存。点击按钮会按当前配置重新生成已有分析结果。"}
          </p>
        </div>
        <button
          className="primary-button embedding-regenerate-button"
          disabled={isLoading || isSaving || !selectedApiConfigId}
          onClick={onRegenerateVectors}
          type="button"
        >
          <RefreshCw size={15} />
          {isSaving ? "处理中" : hasUnsavedSettings ? "保存并重新生成" : "重新生成向量"}
        </button>
      </div>
    </div>
  );
}

function clampSegmentSize(value: string) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return 1;
  return Math.min(12, Math.max(1, parsed));
}
