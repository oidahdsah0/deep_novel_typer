import { DebugClient } from "@/features/debug/DebugClient";
import { getDebugSnapshot } from "@/lib/api/index";

export default async function DebugPage({
  searchParams,
}: {
  searchParams: Promise<{ project_id?: string; return_project_id?: string }>;
}) {
  const params = await searchParams;
  const activeProjectId = params.project_id ?? null;
  const returnProjectId = params.return_project_id ?? activeProjectId;
  const snapshot = await getDebugSnapshot(activeProjectId);

  return (
    <DebugClient
      activeProjectId={activeProjectId}
      returnProjectId={returnProjectId}
      initialSnapshot={snapshot}
    />
  );
}
