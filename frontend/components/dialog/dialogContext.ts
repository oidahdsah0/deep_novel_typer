"use client";

import { createContext, useContext } from "react";
import type { DialogApi } from "./dialogTypes";

export const DialogContext = createContext<DialogApi | null>(null);

export function useConfirm() {
  return useDialogApi().confirm;
}

export function usePrompt() {
  return useDialogApi().prompt;
}

export function useNotice() {
  return useDialogApi().notice;
}

function useDialogApi() {
  const api = useContext(DialogContext);
  if (!api) {
    throw new Error("Dialog hooks must be used inside DialogProvider");
  }
  return api;
}
