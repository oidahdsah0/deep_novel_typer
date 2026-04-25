"use client";

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useState } from "react";
import {
  createChapterNode,
  deleteChapterNode,
  getWorkspaceSnapshot,
  moveChapterNode,
  searchChapters,
  updateChapterNode,
  type ChapterNode,
  type ChapterSearchResult,
} from "@/lib/api/index";
import { useConfirm, useNotice } from "@/components/dialog";
import { chapterResourceSnapshot } from "../resourceControllerState";
import {
  collectChapterIds,
  insertChapterNode,
  updateChapterNodeInTree,
} from "../treeUtils";
import type { ChapterDraftState } from "../types";
import { confirmChapterNodeDelete } from "../workspaceDialogHelpers";
import type { WorkspaceResourceControllerApi } from "./useWorkspaceResourceController";

type ChapterTreeMoveTarget = { parentId: string | null; beforeNodeId: string | null };

export type ChapterTreeActionsApi = {
  chapterDraft: ChapterDraftState | null;
  chapterSearchQuery: string;
  chapterSearchResults: ChapterSearchResult[];
  expandedChapterIds: Set<string>;
  handleDeleteChapterNode: (node: ChapterNode) => Promise<void>;
  handleMoveChapterNode: (nodeId: string, target: ChapterTreeMoveTarget) => Promise<void>;
  handleRenameChapterNode: (node: ChapterNode) => void;
  handleStartCreateChapterNode: (type: "folder" | "chapter", parentId?: string | null) => void;
  handleSubmitChapterDraft: () => Promise<void>;
  isChapterDraftSaving: boolean;
  isChapterSearchLoading: boolean;
  openChapter: (chapterId: string) => Promise<void>;
  openChapterNode: (node: ChapterNode) => Promise<void>;
  setChapterDraft: Dispatch<SetStateAction<ChapterDraftState | null>>;
  setChapterSearchQuery: Dispatch<SetStateAction<string>>;
};

export function useChapterTreeActions({
  flushChapterWritingSynopsis,
  projectId,
  resourceController,
}: {
  flushChapterWritingSynopsis: () => Promise<void>;
  projectId: string;
  resourceController: WorkspaceResourceControllerApi;
}) {
  const {
    handleResourceDeleted,
    handleResourceRenamed,
    openWorkspaceChapter,
    requestSave,
    resource,
    setWorkspace,
  } = resourceController;
  const [chapterDraft, setChapterDraft] = useState<ChapterDraftState | null>(null);
  const [isChapterDraftSaving, setIsChapterDraftSaving] = useState(false);
  const [expandedChapterIds, setExpandedChapterIds] = useState<Set<string>>(() => new Set());
  const [chapterSearchQuery, setChapterSearchQuery] = useState("");
  const [chapterSearchResults, setChapterSearchResults] = useState<ChapterSearchResult[]>([]);
  const [isChapterSearchLoading, setIsChapterSearchLoading] = useState(false);
  const confirm = useConfirm();
  const notice = useNotice();

  useEffect(() => {
    const query = chapterSearchQuery.trim();
    if (!query) {
      setChapterSearchResults([]);
      setIsChapterSearchLoading(false);
      return;
    }

    let isCancelled = false;
    setIsChapterSearchLoading(true);
    const timer = window.setTimeout(() => {
      void searchChapters(projectId, query)
        .then((response) => {
          if (!isCancelled) {
            setChapterSearchResults(response.results);
          }
        })
        .catch(() => {
          if (!isCancelled) {
            setChapterSearchResults([]);
          }
        })
        .finally(() => {
          if (!isCancelled) {
            setIsChapterSearchLoading(false);
          }
        });
    }, 280);

    return () => {
      isCancelled = true;
      window.clearTimeout(timer);
    };
  }, [chapterSearchQuery, projectId]);

  function toggleChapterFolder(nodeId: string) {
    setExpandedChapterIds((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }

  async function flushAndSaveActiveResource() {
    await flushChapterWritingSynopsis();
    await requestSave();
  }

  async function openChapter(chapterId: string) {
    await flushAndSaveActiveResource();
    const nextWorkspace = await getWorkspaceSnapshot(projectId, chapterId);
    openWorkspaceChapter(nextWorkspace);
  }

  async function openChapterNode(node: ChapterNode) {
    if (node.type === "folder") {
      toggleChapterFolder(node.id);
      return;
    }
    if (node.chapter_id) {
      await openChapter(node.chapter_id);
    }
  }

  function handleStartCreateChapterNode(type: "folder" | "chapter", parentId: string | null = null) {
    const fallbackTitle = type === "folder" ? "新章节目录" : "新章节";
    setChapterDraft({ mode: "create", type, parentId, title: fallbackTitle });
    if (parentId) {
      setExpandedChapterIds((current) => new Set(current).add(parentId));
    }
  }

  function handleRenameChapterNode(node: ChapterNode) {
    setChapterDraft({ mode: "rename", node, title: node.title });
  }

  async function handleMoveChapterNode(nodeId: string, target: ChapterTreeMoveTarget) {
    try {
      await flushAndSaveActiveResource();
      const response = await moveChapterNode(projectId, nodeId, {
        parent_id: target.parentId,
        before_node_id: target.beforeNodeId,
      });
      setWorkspace((current) => ({
        ...current,
        chapters: response.chapters,
        chapter_tree: response.chapter_tree,
      }));
      const targetParentId = target.parentId;
      if (targetParentId) {
        setExpandedChapterIds((current) => new Set(current).add(targetParentId));
      }
    } catch (error) {
      void notice(error instanceof Error ? error.message : "移动章节失败", {
        title: "移动章节失败",
      });
      const nextWorkspace = await getWorkspaceSnapshot(
        projectId,
        resource.type === "chapter" ? resource.id : undefined,
      );
      setWorkspace(nextWorkspace);
    }
  }

  async function handleSubmitChapterDraft() {
    if (!chapterDraft) {
      return;
    }
    const title = chapterDraft.title.trim();
    if (!title) {
      return;
    }

    setIsChapterDraftSaving(true);
    try {
      if (chapterDraft.mode === "create") {
        await flushAndSaveActiveResource();
        const node = await createChapterNode(projectId, {
          type: chapterDraft.type,
          title,
          parent_id: chapterDraft.parentId,
        });
        if (chapterDraft.type === "folder") {
          setWorkspace((current) => ({
            ...current,
            chapter_tree: insertChapterNode(current.chapter_tree, node, chapterDraft.parentId),
          }));
          setExpandedChapterIds((current) => new Set(current).add(node.id));
          setChapterDraft(null);
          return;
        }

        const nextWorkspace = await getWorkspaceSnapshot(projectId, node.chapter_id ?? undefined);
        openWorkspaceChapter(nextWorkspace);
        setChapterDraft(null);
        return;
      }

      const updated = await updateChapterNode(projectId, chapterDraft.node.id, { title });
      setWorkspace((current) => ({
        ...current,
        chapters: updated.chapter_id
          ? current.chapters.map((chapter) =>
              chapter.id === updated.chapter_id ? { ...chapter, title: updated.title } : chapter,
            )
          : current.chapters,
        chapter_tree: updateChapterNodeInTree(current.chapter_tree, updated),
      }));
      if (resource.type === "chapter" && resource.id === updated.chapter_id) {
        handleResourceRenamed({ type: "chapter", id: resource.id, title: updated.title });
      }
      setChapterDraft(null);
    } finally {
      setIsChapterDraftSaving(false);
    }
  }

  async function handleDeleteChapterNode(node: ChapterNode) {
    if (!(await confirmChapterNodeDelete(confirm, node))) {
      return;
    }

    try {
      await flushAndSaveActiveResource();
      await deleteChapterNode(projectId, node.id);
      const deletedChapterIds = collectChapterIds(node);
      const keepCurrentChapter =
        resource.type === "chapter" && !deletedChapterIds.has(resource.id);
      const nextWorkspace = await getWorkspaceSnapshot(
        projectId,
        keepCurrentChapter ? resource.id : undefined,
      );
      handleResourceDeleted(
        nextWorkspace,
        resource.type === "chapter" ? chapterResourceSnapshot(nextWorkspace) : undefined,
      );
      setChapterSearchResults([]);
    } catch (error) {
      void notice(error instanceof Error ? error.message : "删除章节失败", {
        title: "删除章节失败",
      });
    }
  }

  return {
    chapterDraft,
    chapterSearchQuery,
    chapterSearchResults,
    expandedChapterIds,
    handleDeleteChapterNode,
    handleMoveChapterNode,
    handleRenameChapterNode,
    handleStartCreateChapterNode,
    handleSubmitChapterDraft,
    isChapterDraftSaving,
    isChapterSearchLoading,
    openChapter,
    openChapterNode,
    setChapterDraft,
    setChapterSearchQuery,
  } satisfies ChapterTreeActionsApi;
}
