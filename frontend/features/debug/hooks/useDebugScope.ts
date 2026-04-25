import { buildDebugHref } from "../debugTypes";

export function useDebugScope({
  activeProjectId,
  returnProjectId,
}: {
  activeProjectId: string | null;
  returnProjectId: string | null;
}) {
  const sourceProjectId = returnProjectId ?? activeProjectId;
  const scoped = Boolean(activeProjectId);
  return {
    allDebugHref: buildDebugHref(null, sourceProjectId),
    backHref: sourceProjectId ? `/projects/${encodeURIComponent(sourceProjectId)}` : "/",
    projectDebugHref: sourceProjectId
      ? buildDebugHref(sourceProjectId, sourceProjectId)
      : "/debug",
    scoped,
    sourceProjectId,
  };
}
