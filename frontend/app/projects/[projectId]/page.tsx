import { WorkspaceClient } from "@/app/workspace-client";
import { ApiFetchError, getWorkspaceSnapshot } from "@/lib/api/index";
import { notFound } from "next/navigation";

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  let workspace;
  try {
    workspace = await getWorkspaceSnapshot(projectId);
  } catch (error) {
    if (error instanceof ApiFetchError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  return <WorkspaceClient initialWorkspace={workspace} />;
}
