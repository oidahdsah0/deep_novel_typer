"use client";

import { ArrowLeft, BookOpen, FilePlus2, FolderPlus, Layers3 } from "lucide-react";
import Link from "next/link";
import type { Dispatch, PointerEvent, ReactNode, SetStateAction } from "react";
import type {
  ChapterNode,
  DocumentNode,
  ProjectSearchResult,
  ProjectSearchScope,
  WorkspaceSnapshot,
} from "@/lib/api/index";
import { ChapterDraftForm } from "@/features/workspace/components/chapters/ChapterDraftForm";
import { ChapterTree } from "@/features/workspace/components/chapters/ChapterTree";
import { DocumentDraftForm } from "@/features/workspace/components/documents/DocumentDraftForm";
import { DocumentTree } from "@/features/workspace/components/documents/DocumentTree";
import { ProjectSearchPanel } from "@/features/workspace/components/search/ProjectSearchPanel";
import type { ProjectSearchGroup } from "@/features/workspace/hooks/useProjectSearch";
import type {
  ActiveResource,
  ChapterDraftState,
  DocumentDraftState,
} from "@/features/workspace/types";

type WorkspaceProjectRailProps = {
  activeResource: ActiveResource;
  chapterDraft: ChapterDraftState | null;
  documentDraft: DocumentDraftState | null;
  expandedChapterIds: Set<string>;
  expandedDocumentIds: Set<string>;
  isChapterDraftSaving: boolean;
  isDocumentDraftSaving: boolean;
  isProjectSearchLoading: boolean;
  onDeleteChapterNode: (node: ChapterNode) => void;
  onDeleteDocumentNode: (node: DocumentNode) => void;
  onMoveChapterNode: Parameters<typeof ChapterTree>[0]["onMoveNode"];
  onMoveDocumentNode: Parameters<typeof DocumentTree>[0]["onMoveNode"];
  onOpenChapterNode: Parameters<typeof ChapterTree>[0]["onOpenNode"];
  onOpenDocument: Parameters<typeof DocumentTree>[0]["onOpenDocument"];
  onOpenSearchResult: (result: ProjectSearchResult) => void;
  onRenameChapterNode: Parameters<typeof ChapterTree>[0]["onRenameNode"];
  onRenameDocumentNode: Parameters<typeof DocumentTree>[0]["onRenameNode"];
  onResizeStart: (event: PointerEvent<HTMLButtonElement>) => void;
  onStartCreateChapterNode: Parameters<typeof ChapterTree>[0]["onCreateNode"];
  onStartCreateDocumentNode: Parameters<typeof DocumentTree>[0]["onCreateNode"];
  onSubmitChapterDraft: () => void;
  onSubmitDocumentDraft: () => void;
  projectSearchGroups: ProjectSearchGroup[];
  projectSearchQuery: string;
  projectSearchScope: ProjectSearchScope;
  setChapterDraft: Dispatch<SetStateAction<ChapterDraftState | null>>;
  setDocumentDraft: Dispatch<SetStateAction<DocumentDraftState | null>>;
  setProjectSearchQuery: (query: string) => void;
  setProjectSearchScope: (scope: ProjectSearchScope) => void;
  workspace: WorkspaceSnapshot;
};

export function WorkspaceProjectRail({
  activeResource,
  chapterDraft,
  documentDraft,
  expandedChapterIds,
  expandedDocumentIds,
  isChapterDraftSaving,
  isDocumentDraftSaving,
  isProjectSearchLoading,
  onDeleteChapterNode,
  onDeleteDocumentNode,
  onMoveChapterNode,
  onMoveDocumentNode,
  onOpenChapterNode,
  onOpenDocument,
  onOpenSearchResult,
  onRenameChapterNode,
  onRenameDocumentNode,
  onResizeStart,
  onStartCreateChapterNode,
  onStartCreateDocumentNode,
  onSubmitChapterDraft,
  onSubmitDocumentDraft,
  projectSearchGroups,
  projectSearchQuery,
  projectSearchScope,
  setChapterDraft,
  setDocumentDraft,
  setProjectSearchQuery,
  setProjectSearchScope,
  workspace,
}: WorkspaceProjectRailProps) {
  return (
    <aside className="project-rail" aria-label="项目导航">
      <button
        aria-label="拖拽调整左侧栏宽度"
        className="rail-resize-handle"
        onPointerDown={onResizeStart}
        type="button"
      />
      <div className="rail-hero">
        <Link className="back-link" href="/">
          <ArrowLeft size={16} />
          小说库
        </Link>
        <div className="brand-row project-identity">
          <div className="brand-mark">D</div>
          <div>
            <p className="eyebrow">{workspace.project.genre || "Novel"}</p>
            <h1>{workspace.project.title}</h1>
          </div>
        </div>
      </div>

      <ProjectSearchPanel
        groups={projectSearchGroups}
        isLoading={isProjectSearchLoading}
        onOpenResult={onOpenSearchResult}
        query={projectSearchQuery}
        scope={projectSearchScope}
        setQuery={setProjectSearchQuery}
        setScope={setProjectSearchScope}
      />
      <WorkspaceTreeSection
        icon={<BookOpen size={16} />}
        onCreateFile={() => onStartCreateChapterNode("chapter")}
        onCreateFolder={() => onStartCreateChapterNode("folder")}
        title="章节"
      >
        <ChapterDraftForm
          draft={chapterDraft}
          isSaving={isChapterDraftSaving}
          onCancel={() => setChapterDraft(null)}
          onChange={(title) =>
            setChapterDraft((current) => (current ? { ...current, title } : current))
          }
          onSubmit={onSubmitChapterDraft}
        />
        <ChapterTree
          activeChapterId={activeResource.type === "chapter" ? activeResource.id : null}
          expandedIds={expandedChapterIds}
          nodes={workspace.chapter_tree}
          onCreateNode={onStartCreateChapterNode}
          onDeleteNode={onDeleteChapterNode}
          onMoveNode={onMoveChapterNode}
          onOpenNode={onOpenChapterNode}
          onRenameNode={onRenameChapterNode}
        />
      </WorkspaceTreeSection>

      <WorkspaceTreeSection
        icon={<Layers3 size={16} />}
        onCreateFile={() => onStartCreateDocumentNode("markdown")}
        onCreateFolder={() => onStartCreateDocumentNode("folder")}
        title="资料"
      >
        <DocumentDraftForm
          draft={documentDraft}
          isSaving={isDocumentDraftSaving}
          onCancel={() => setDocumentDraft(null)}
          onChange={(title) =>
            setDocumentDraft((current) => (current ? { ...current, title } : current))
          }
          onSubmit={onSubmitDocumentDraft}
        />
        <DocumentTree
          activeDocumentId={activeResource.type === "document" ? activeResource.id : null}
          expandedIds={expandedDocumentIds}
          nodes={workspace.document_tree}
          onCreateNode={onStartCreateDocumentNode}
          onDeleteNode={onDeleteDocumentNode}
          onMoveNode={onMoveDocumentNode}
          onOpenDocument={onOpenDocument}
          onRenameNode={onRenameDocumentNode}
        />
      </WorkspaceTreeSection>
    </aside>
  );
}

function WorkspaceTreeSection({
  children,
  icon,
  onCreateFile,
  onCreateFolder,
  title,
}: {
  children: ReactNode;
  icon: ReactNode;
  onCreateFile: () => void;
  onCreateFolder: () => void;
  title: string;
}) {
  return (
    <section className="rail-section">
      <div className="section-title with-actions">
        <span>
          {icon}
          {title}
        </span>
        <div className="section-tools">
          <button
            aria-label={`新建${title}目录`}
            className="tiny-tool"
            onClick={onCreateFolder}
            type="button"
          >
            <FolderPlus size={14} />
          </button>
          <button
            aria-label={title === "章节" ? "新建章节" : "新建 Markdown 文本"}
            className="tiny-tool"
            onClick={onCreateFile}
            type="button"
          >
            <FilePlus2 size={14} />
          </button>
        </div>
      </div>
      {children}
    </section>
  );
}
