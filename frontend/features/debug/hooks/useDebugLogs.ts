"use client";

import { useState } from "react";
import {
  clearDebugAll,
  clearDebugRequestLogs,
  clearDebugTokenUsage,
  getDebugSnapshot,
  type DebugSnapshot,
} from "@/lib/api/index";
import { useConfirm } from "@/components/dialog";

export function useDebugLogs({
  activeProjectId,
  initialSnapshot,
}: {
  activeProjectId: string | null;
  initialSnapshot: DebugSnapshot;
}) {
  const [snapshot, setSnapshot] = useState(initialSnapshot);
  const [expandedId, setExpandedId] = useState(snapshot.request_logs[0]?.id ?? "");
  const [isPending, setIsPending] = useState(false);
  const confirm = useConfirm();
  const scoped = Boolean(activeProjectId);
  const expandedLog = snapshot.request_logs.find((log) => log.id === expandedId) ?? null;

  function applySnapshot(nextSnapshot: DebugSnapshot) {
    setSnapshot(nextSnapshot);
    setExpandedId((current) =>
      nextSnapshot.request_logs.some((log) => log.id === current)
        ? current
        : nextSnapshot.request_logs[0]?.id ?? "",
    );
  }

  async function runPending(action: () => Promise<void>) {
    setIsPending(true);
    try {
      await action();
    } finally {
      setIsPending(false);
    }
  }

  function refresh() {
    void runPending(async () => {
      applySnapshot(await getDebugSnapshot(activeProjectId));
    });
  }

  async function clearTokenUsage() {
    if (
      !(await confirm(scoped ? "确认清空当前项目的 Token 统计？" : "确认清空全部 Token 统计？", {
        confirmLabel: "清空",
        tone: "danger",
      }))
    ) {
      return;
    }
    void runPending(async () => {
      await clearDebugTokenUsage(activeProjectId);
      applySnapshot(await getDebugSnapshot(activeProjectId));
    });
  }

  async function clearRequestLogs() {
    if (
      !(await confirm(scoped ? "确认清空当前项目的请求 Log？" : "确认清空全部请求 Log？", {
        confirmLabel: "清空",
        tone: "danger",
      }))
    ) {
      return;
    }
    void runPending(async () => {
      await clearDebugRequestLogs(activeProjectId);
      applySnapshot(await getDebugSnapshot(activeProjectId));
    });
  }

  async function clearAll() {
    if (
      !(await confirm(scoped ? "确认清空当前项目的全部 Debug 数据？" : "确认清空全部 Debug 数据？", {
        confirmLabel: "清空全部",
        tone: "danger",
      }))
    ) {
      return;
    }
    void runPending(async () => {
      await clearDebugAll(activeProjectId);
      applySnapshot(await getDebugSnapshot(activeProjectId));
    });
  }

  return {
    clearAll,
    clearRequestLogs,
    clearTokenUsage,
    expandedId,
    expandedLog,
    isPending,
    refresh,
    setExpandedId,
    snapshot,
  };
}
