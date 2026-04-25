"use client";

import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { DialogContext } from "./dialogContext";
import { DialogView } from "./DialogView";
import type {
  ConfirmRequest,
  DialogApi,
  DialogRequest,
  DialogRequestInput,
  NoticeRequest,
  PromptRequest,
} from "./dialogTypes";

export function DialogProvider({ children }: { children: ReactNode }) {
  const [queue, setQueue] = useState<DialogRequest[]>([]);
  const [promptValue, setPromptValue] = useState("");
  const nextIdRef = useRef(1);
  const confirmButtonRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const promptInputRef = useRef<HTMLInputElement>(null);
  const noticeButtonRef = useRef<HTMLButtonElement>(null);
  const active = queue[0] ?? null;

  const enqueue = useCallback((request: DialogRequestInput) => {
    const id = nextIdRef.current;
    nextIdRef.current += 1;
    setQueue((current) => [...current, { ...request, id } as DialogRequest]);
  }, []);

  const confirm = useCallback<DialogApi["confirm"]>(
    (message, options = {}) =>
      new Promise<boolean>((resolve) => {
        enqueue({ kind: "confirm", message, options, resolve });
      }),
    [enqueue],
  );

  const prompt = useCallback<DialogApi["prompt"]>(
    (message, defaultValue = "", options = {}) =>
      new Promise<string | null>((resolve) => {
        enqueue({ kind: "prompt", message, defaultValue, options, resolve });
      }),
    [enqueue],
  );

  const notice = useCallback<DialogApi["notice"]>(
    (message, options = {}) =>
      new Promise<void>((resolve) => {
        enqueue({ kind: "notice", message, options, resolve: () => resolve() });
      }),
    [enqueue],
  );

  const api = useMemo(() => ({ confirm, notice, prompt }), [confirm, notice, prompt]);

  const removeActive = useCallback((request: DialogRequest) => {
    setQueue((current) => current.filter((item) => item.id !== request.id));
  }, []);

  const cancelActive = useCallback(() => {
    if (!active) return;
    if (active.kind === "confirm") {
      active.resolve(false);
    } else if (active.kind === "prompt") {
      active.resolve(null);
    } else {
      active.resolve();
    }
    removeActive(active);
  }, [active, removeActive]);

  useEffect(() => {
    if (!active) return;
    if (active.kind === "prompt") {
      setPromptValue(active.defaultValue);
      window.setTimeout(() => promptInputRef.current?.focus(), 0);
    } else if (active.kind === "confirm") {
      window.setTimeout(() => confirmButtonRef.current?.focus(), 0);
    } else {
      window.setTimeout(() => noticeButtonRef.current?.focus(), 0);
    }
  }, [active]);

  useEffect(() => {
    if (!active) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        cancelActive();
      } else if (event.key === "Tab") {
        trapDialogFocus(event, dialogRef.current);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [active, cancelActive]);

  function resolveConfirm(request: ConfirmRequest, value: boolean) {
    request.resolve(value);
    removeActive(request);
  }

  function resolvePrompt(request: PromptRequest, value: string | null) {
    request.resolve(value);
    removeActive(request);
  }

  function resolveNotice(request: NoticeRequest) {
    request.resolve();
    removeActive(request);
  }

  function resolvePromptSubmit(request: PromptRequest) {
    resolvePrompt(request, promptValue.trim());
  }

  return (
    <DialogContext.Provider value={api}>
      {children}
      <DialogView
        active={active}
        confirmButtonRef={confirmButtonRef}
        dialogRef={dialogRef}
        noticeButtonRef={noticeButtonRef}
        onConfirm={resolveConfirm}
        onNotice={resolveNotice}
        onPromptCancel={(request) => resolvePrompt(request, null)}
        onPromptChange={setPromptValue}
        onPromptSubmit={resolvePromptSubmit}
        promptInputRef={promptInputRef}
        promptValue={promptValue}
      />
    </DialogContext.Provider>
  );
}

function trapDialogFocus(event: KeyboardEvent, root: HTMLDivElement | null) {
  const focusable = root?.querySelectorAll<HTMLElement>(
    'button, input, select, textarea, [href], [tabindex]:not([tabindex="-1"])',
  );
  if (!focusable?.length) return;

  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
