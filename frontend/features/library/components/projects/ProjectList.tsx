import type { ProjectSummary } from "@/lib/api/index";
import { ProjectCard } from "@/features/library/components/ProjectCard";

export function ProjectList({
  onDelete,
  onExport,
  onOpen,
  onSelect,
  projects,
  selectedId,
}: {
  onDelete: (project: ProjectSummary) => void;
  onExport: (project: ProjectSummary) => void;
  onOpen: (project: ProjectSummary) => void;
  onSelect: (projectId: string) => void;
  projects: ProjectSummary[];
  selectedId: string;
}) {
  return (
    <div className="project-grid project-summary-grid">
      {projects.map((project) => (
        <ProjectCard
          isSelected={project.id === selectedId}
          key={project.id}
          onDelete={() => onDelete(project)}
          onExport={() => onExport(project)}
          onOpen={() => onOpen(project)}
          onSelect={() => onSelect(project.id)}
          project={project}
        />
      ))}
    </div>
  );
}
