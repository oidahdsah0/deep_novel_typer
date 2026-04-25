"use client";

import type { Dispatch, SetStateAction } from "react";
import { useState } from "react";
import {
  createDocumentNode,
  deleteDocumentNode,
  getDocument,
  getWorkspaceSnapshot,
  moveDocumentNode,
  updateDocumentNode,
  type DocumentDetail,
  type DocumentNode,
} from "@/lib/api/index";
import { useConfirm, useNotice } from "@/components/dialog";
import { documentResourceSnapshot } from "../resourceControllerState";
import {
  collectDocumentIds,
  insertDocumentNode,
  summarizeDocumentDelete,
  updateDocumentNodeInTree,
} from "../treeUtils";
import type { DocumentDraftState } from "../types";
import type { WorkspaceResourceControllerApi } from "./useWorkspaceResourceController";

export type DocumentTreeActionsApi = {
  documentDraft: DocumentDraftState | null;
  expandedDocumentIds: Set<string>;
  handleDeleteDocumentNode: (document: DocumentNode) => Promise<void>;
  handleMoveDocumentNode: (
    nodeId: string,
    target: { parentId: string | null; beforeNodeId: string | null },
  ) => Promise<void>;
  handleRenameDocumentNode: (document: DocumentNode) => void;
  handleStartCreateDocumentNode: (
    type: "folder" | "markdown",
    parentId?: string | null,
  ) => void;
  handleSubmitDocumentDraft: () => Promise<void>;
  isDocumentDraftSaving: boolean;
  openDocument: (document: DocumentNode) => Promise<void>;
  setDocumentDraft: Dispatch<SetStateAction<DocumentDraftState | null>>;
  toggleDocumentFolder: (documentId: string) => void;
};

export function useDocumentTreeActions({
  flushChapterWritingSynopsis,
  projectId,
  resourceController,
}: {
  flushChapterWritingSynopsis: () => Promise<void>;
  projectId: string;
  resourceController: WorkspaceResourceControllerApi;
}) {
  const {
    handleResourceRenamed,
    openResource,
    openWorkspaceChapter,
    requestSave,
    resource,
    setWorkspace,
  } = resourceController;
  const [documentDraft, setDocumentDraft] = useState<DocumentDraftState | null>(null);
  const [isDocumentDraftSaving, setIsDocumentDraftSaving] = useState(false);
  const [expandedDocumentIds, setExpandedDocumentIds] = useState<Set<string>>(() => new Set());
  const confirm = useConfirm();
  const notice = useNotice();

  async function openDocument(document: DocumentNode) {
    if (document.type === "folder") {
      toggleDocumentFolder(document.id);
      return;
    }
    await flushChapterWritingSynopsis();
    await requestSave();
    const detail: DocumentDetail = await getDocument(projectId, document.id);
    openResource(documentResourceSnapshot(detail));
  }

  function toggleDocumentFolder(documentId: string) {
    setExpandedDocumentIds((current) => {
      const next = new Set(current);
      if (next.has(documentId)) {
        next.delete(documentId);
      } else {
        next.add(documentId);
      }
      return next;
    });
  }

  function handleStartCreateDocumentNode(
    type: "folder" | "markdown",
    parentId: string | null = null,
  ) {
    const fallbackTitle = type === "folder" ? "新资料夹" : "新 Markdown";
    setDocumentDraft({ mode: "create", type, parentId, title: fallbackTitle });
    if (parentId) {
      setExpandedDocumentIds((current) => new Set(current).add(parentId));
    }
  }

  function handleRenameDocumentNode(document: DocumentNode) {
    setDocumentDraft({ mode: "rename", node: document, title: document.title });
  }

  async function handleMoveDocumentNode(
    nodeId: string,
    target: { parentId: string | null; beforeNodeId: string | null },
  ) {
    try {
      await flushChapterWritingSynopsis();
      await requestSave();
      const response = await moveDocumentNode(projectId, nodeId, {
        parent_id: target.parentId,
        before_node_id: target.beforeNodeId,
      });
      setWorkspace((current) => ({
        ...current,
        document_tree: response.document_tree,
      }));
      const targetParentId = target.parentId;
      if (targetParentId) {
        setExpandedDocumentIds((current) => new Set(current).add(targetParentId));
      }
    } catch (error) {
      void notice(error instanceof Error ? error.message : "移动资料失败", {
        title: "移动资料失败",
      });
      const nextWorkspace = await getWorkspaceSnapshot(
        projectId,
        resource.type === "chapter" ? resource.id : undefined,
      );
      setWorkspace(nextWorkspace);
    }
  }

  async function handleSubmitDocumentDraft() {
    if (!documentDraft) {
      return;
    }
    const title = documentDraft.title.trim();
    if (!title) {
      return;
    }

    setIsDocumentDraftSaving(true);
    try {
      if (documentDraft.mode === "create") {
        const node = await createDocumentNode(projectId, {
          type: documentDraft.type,
          title,
          parent_id: documentDraft.parentId,
        });
        setWorkspace((current) => ({
          ...current,
          document_tree: insertDocumentNode(current.document_tree, node, documentDraft.parentId),
        }));
        if (documentDraft.type === "folder") {
          setExpandedDocumentIds((current) => new Set(current).add(node.id));
          setDocumentDraft(null);
          return;
        }

        await flushChapterWritingSynopsis();
        await requestSave();
        const detail = await getDocument(projectId, node.id);
        openResource(documentResourceSnapshot(detail));
        setDocumentDraft(null);
        return;
      }

      const updated = await updateDocumentNode(projectId, documentDraft.node.id, { title });
      setWorkspace((current) => ({
        ...current,
        document_tree: updateDocumentNodeInTree(current.document_tree, updated),
      }));
      if (resource.type === "document" && resource.id === updated.id) {
        handleResourceRenamed({ type: "document", id: updated.id, title: updated.title });
      }
      setDocumentDraft(null);
    } finally {
      setIsDocumentDraftSaving(false);
    }
  }

  async function handleDeleteDocumentNode(document: DocumentNode) {
    const impact = summarizeDocumentDelete(document);
    const message =
      document.type === "folder"
        ? `删除资料目录「${document.title}」？\n\n将删除 ${impact.folders} 个目录、${impact.documents} 个 Markdown 文本，文件会移入本地 trash。`
        : `删除资料「${document.title}」？\n\nMarkdown 文件会移入本地 trash。`;
    if (
      !(await confirm(message, {
        confirmLabel: "删除",
        tone: "danger",
      }))
    ) {
      return;
    }

    try {
      await flushChapterWritingSynopsis();
      await requestSave();
      await deleteDocumentNode(projectId, document.id);
      const deletedDocumentIds = collectDocumentIds(document);
      const deletedActiveDocument =
        resource.type === "document" && deletedDocumentIds.has(resource.id);
      const nextWorkspace = await getWorkspaceSnapshot(
        projectId,
        resource.type === "chapter" ? resource.id : undefined,
      );
      setWorkspace(nextWorkspace);
      if (deletedActiveDocument) {
        openWorkspaceChapter(nextWorkspace);
      }
    } catch (error) {
      void notice(error instanceof Error ? error.message : "删除资料失败", {
        title: "删除资料失败",
      });
    }
  }

  return {
    documentDraft,
    expandedDocumentIds,
    handleDeleteDocumentNode,
    handleMoveDocumentNode,
    handleRenameDocumentNode,
    handleStartCreateDocumentNode,
    handleSubmitDocumentDraft,
    isDocumentDraftSaving,
    openDocument,
    setDocumentDraft,
    toggleDocumentFolder,
  } satisfies DocumentTreeActionsApi;
}
