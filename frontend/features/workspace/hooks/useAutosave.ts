"use client";

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useTransition } from "react";
import type { SaveState } from "../types";

export function useAutosave({
  content,
  disabled = false,
  saveActive,
  savedContent,
  setSaveState,
}: {
  content: string;
  disabled?: boolean;
  saveActive: (nextContent?: string) => Promise<void>;
  savedContent: string;
  setSaveState: Dispatch<SetStateAction<SaveState>>;
}) {
  const [, startTransition] = useTransition();

  useEffect(() => {
    if (disabled) {
      return;
    }

    if (content === savedContent) {
      return;
    }

    setSaveState("saving");
    const timer = window.setTimeout(() => {
      startTransition(() => {
        void saveActive(content);
      });
    }, 900);

    return () => window.clearTimeout(timer);
  }, [content, disabled, saveActive, savedContent, setSaveState]);
}
