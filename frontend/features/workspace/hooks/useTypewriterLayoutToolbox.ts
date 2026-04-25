"use client";

import { useEffect, useState } from "react";
import type {
  TypewriterLayoutSettings,
  TypewriterLayoutSettingsInput,
} from "@/lib/api/index";
import { updateTypewriterLayoutSettings } from "@/lib/api/index";
import type { TypewriterLayoutToolboxApi } from "./workspaceToolApiTypes";

export type { TypewriterLayoutToolboxApi } from "./workspaceToolApiTypes";

const defaultSettings: TypewriterLayoutSettings = {
  first_line_indent_chars: 0,
  font_size_px: 20,
  paragraph_gap_lines: 0,
  line_height_multiplier: 2.9,
  updated_at: null,
};

export function useTypewriterLayoutToolbox(
  initialSettings: TypewriterLayoutSettings | null | undefined,
) {
  const resolvedInitial = normalizeSettings(initialSettings ?? defaultSettings);
  const [isOpen, setIsOpen] = useState(false);
  const [savedSettings, setSavedSettings] = useState<TypewriterLayoutSettings>(resolvedInitial);
  const [draftSettings, setDraftSettings] = useState<TypewriterLayoutSettingsInput>(
    inputFromSettings(resolvedInitial),
  );
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) setDraftSettings(inputFromSettings(savedSettings));
  }, [isOpen, savedSettings]);

  async function saveSettings() {
    setIsSaving(true);
    setError(null);
    setNotice(null);
    try {
      const response = await updateTypewriterLayoutSettings(normalizeInput(draftSettings));
      const normalized = normalizeSettings(response);
      setSavedSettings(normalized);
      setDraftSettings(inputFromSettings(normalized));
      setNotice("版式已保存");
    } catch (err) {
      setError(err instanceof Error ? err.message : "版式保存失败");
    } finally {
      setIsSaving(false);
    }
  }

  function resetDraftToDefault() {
    setDraftSettings(inputFromSettings(defaultSettings));
  }

  return {
    draftSettings,
    error,
    hasUnsavedSettings: !sameInput(inputFromSettings(savedSettings), draftSettings),
    isOpen,
    isSaving,
    notice,
    resetDraftToDefault,
    savedSettings,
    saveSettings,
    setDraftSettings,
    setIsOpen,
  } satisfies TypewriterLayoutToolboxApi;
}

function normalizeSettings(settings: TypewriterLayoutSettings): TypewriterLayoutSettings {
  return {
    first_line_indent_chars: clampTenth(settings.first_line_indent_chars, 0, 8, 0),
    font_size_px: clampInteger(settings.font_size_px, 12, 32, 20),
    paragraph_gap_lines: clampTenth(settings.paragraph_gap_lines, 0, 5, 0),
    line_height_multiplier: clampTenth(settings.line_height_multiplier, 1, 4, 2.9),
    updated_at: settings.updated_at ?? null,
  };
}

function normalizeInput(input: TypewriterLayoutSettingsInput): TypewriterLayoutSettingsInput {
  return {
    first_line_indent_chars: clampTenth(input.first_line_indent_chars, 0, 8, 0),
    font_size_px: clampInteger(input.font_size_px, 12, 32, 20),
    paragraph_gap_lines: clampTenth(input.paragraph_gap_lines, 0, 5, 0),
    line_height_multiplier: clampTenth(input.line_height_multiplier, 1, 4, 2.9),
  };
}

function inputFromSettings(settings: TypewriterLayoutSettings): TypewriterLayoutSettingsInput {
  return {
    first_line_indent_chars: settings.first_line_indent_chars,
    font_size_px: settings.font_size_px,
    paragraph_gap_lines: settings.paragraph_gap_lines,
    line_height_multiplier: settings.line_height_multiplier,
  };
}

function sameInput(left: TypewriterLayoutSettingsInput, right: TypewriterLayoutSettingsInput) {
  return (
    left.first_line_indent_chars === right.first_line_indent_chars &&
    left.font_size_px === right.font_size_px &&
    left.paragraph_gap_lines === right.paragraph_gap_lines &&
    left.line_height_multiplier === right.line_height_multiplier
  );
}

function clampInteger(value: number, min: number, max: number, fallback: number) {
  if (!Number.isFinite(value)) return fallback;
  return Math.min(max, Math.max(min, Math.round(value)));
}

function clampTenth(value: number, min: number, max: number, fallback: number) {
  if (!Number.isFinite(value)) return fallback;
  return Math.min(max, Math.max(min, Math.round(value * 10) / 10));
}
