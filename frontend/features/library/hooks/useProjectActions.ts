import type { Dispatch, SetStateAction, TransitionStartFunction } from "react";

import {
  createProject,
  deleteProject,
  openProject,
  updateProject,
  type LibrarySnapshot,
  type ProjectInput,
  type ProjectSummary,
} from "@/lib/api/index";
import { emptyDraft } from "@/features/library/utils";
import { useConfirm } from "@/components/dialog";

export function useProjectActions({
  draft,
  editDraft,
  library,
  navigateToProject,
  selectedProject,
  setDraft,
  setEditDraft,
  setLibrary,
  setSelectedId,
  onProjectCreated,
  startTransition,
}: {
  draft: ProjectInput;
  editDraft: Partial<ProjectInput>;
  library: LibrarySnapshot;
  navigateToProject: (projectId: string) => void;
  onProjectCreated?: () => void;
  selectedProject?: ProjectSummary;
  setDraft: Dispatch<SetStateAction<ProjectInput>>;
  setEditDraft: Dispatch<SetStateAction<Partial<ProjectInput>>>;
  setLibrary: Dispatch<SetStateAction<LibrarySnapshot>>;
  setSelectedId: Dispatch<SetStateAction<string>>;
  startTransition: TransitionStartFunction;
}) {
  const confirm = useConfirm();

  function refreshProject(project: ProjectSummary) {
    setLibrary((current) => ({
      ...current,
      projects: current.projects.map((item) => (item.id === project.id ? project : item)),
    }));
  }

  function handleCreate() {
    if (!draft.title.trim()) {
      return;
    }

    startTransition(async () => {
      const project = await createProject(draft);
      setLibrary((current) => ({
        ...current,
        projects: [project, ...current.projects],
        stats: {
          ...current.stats,
          active_count: current.stats.active_count + 1,
        },
      }));
      setSelectedId(project.id);
      setDraft(emptyDraft);
      onProjectCreated?.();
    });
  }

  function handleUpdate() {
    if (!selectedProject) {
      return;
    }

    startTransition(async () => {
      const updated = await updateProject(selectedProject.id, editDraft);
      refreshProject(updated);
      setEditDraft({});
    });
  }

  function handleOpen(project: ProjectSummary) {
    startTransition(async () => {
      await openProject(project.id);
      navigateToProject(project.id);
    });
  }

  async function handleDelete(project: ProjectSummary) {
    if (
      !(await confirm(`确认将「${project.title}」移入废纸篓？`, {
        confirmLabel: "移入废纸篓",
        tone: "danger",
      }))
    ) {
      return;
    }

    startTransition(async () => {
      await deleteProject(project.id);
      const nextSelectedId =
        library.projects.find((item) => item.id !== project.id)?.id ?? "";
      setLibrary((current) => {
        const projects = current.projects.filter((item) => item.id !== project.id);
        return {
          ...current,
          projects,
          stats: {
            ...current.stats,
            active_count: Math.max(0, current.stats.active_count - 1),
            trash_count: current.stats.trash_count + 1,
          },
        };
      });
      setSelectedId(nextSelectedId);
    });
  }

  return {
    handleCreate,
    handleDelete,
    handleOpen,
    handleUpdate,
  };
}
