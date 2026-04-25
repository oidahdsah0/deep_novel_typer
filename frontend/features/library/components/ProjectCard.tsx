import { Download, FolderOpen, Trash2 } from "lucide-react";

import type { ProjectSummary } from "@/lib/api/index";
import { formatProjectCardSummary, statusLabels } from "@/features/library/utils";

export function ProjectCard({
  isSelected,
  onDelete,
  onExport,
  onOpen,
  onSelect,
  project,
}: {
  isSelected: boolean;
  onDelete: () => void;
  onExport: () => void;
  onOpen: () => void;
  onSelect: () => void;
  project: ProjectSummary;
}) {
  const summarySource = project.description.trim() || project.subtitle.trim() || "还没有简介。";
  const summary = formatProjectCardSummary(summarySource);

  return (
    <article
      className={
        isSelected
          ? "project-card project-card-with-actions project-summary-card active"
          : "project-card project-card-with-actions project-summary-card"
      }
    >
      <button className="project-card-main" onClick={onSelect} type="button">
        <span className="project-card-status">{statusLabels[project.status]}</span>
        <span className="project-card-title">{project.title}</span>
        <span className="project-card-summary">{summary}</span>
        <span className="project-card-meta">
          {project.chapter_count} 章 · {project.word_count} 字
        </span>
      </button>
      <div className="project-card-actions">
        <button
          className="project-card-icon export"
          onClick={onExport}
          type="button"
          aria-label={`导出 ${project.title} 到指定目录`}
          title="导出到指定目录"
        >
          <Download size={15} />
        </button>
        <button
          className="project-card-icon danger"
          onClick={onDelete}
          type="button"
          aria-label={`删除 ${project.title}`}
        >
          <Trash2 size={15} />
        </button>
        <button
          className="project-card-icon"
          onClick={onOpen}
          type="button"
          aria-label={`打开 ${project.title}`}
        >
          <FolderOpen size={15} />
        </button>
      </div>
    </article>
  );
}
