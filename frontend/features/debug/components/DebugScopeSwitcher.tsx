"use client";

import { RefreshCw } from "lucide-react";
import Link from "next/link";

export function DebugScopeSwitcher({
  allDebugHref,
  onRefresh,
  projectDebugHref,
  scoped,
  sourceProjectId,
}: {
  allDebugHref: string;
  onRefresh: () => void;
  projectDebugHref: string;
  scoped: boolean;
  sourceProjectId: string | null;
}) {
  return (
    <div className="debug-header-actions">
      <div className="debug-scope-switch" aria-label="Debug 范围">
        <Link className={scoped ? "" : "active"} href={allDebugHref}>
          全部
        </Link>
        {sourceProjectId ? (
          <Link className={scoped ? "active" : ""} href={projectDebugHref}>
            当前项目
          </Link>
        ) : null}
      </div>
      <button className="icon-button" onClick={onRefresh} type="button" aria-label="刷新">
        <RefreshCw size={16} />
      </button>
    </div>
  );
}
