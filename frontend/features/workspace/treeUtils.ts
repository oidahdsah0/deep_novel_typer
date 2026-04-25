import type { ChapterNode, DocumentNode } from "@/lib/api/index";

export function insertChapterNode(
  nodes: ChapterNode[],
  node: ChapterNode,
  parentId: string | null,
): ChapterNode[] {
  if (!parentId) {
    return [...nodes, { ...node, children: node.children ?? [] }];
  }

  return nodes.map((item) =>
    item.id === parentId
      ? { ...item, children: [...item.children, { ...node, children: node.children ?? [] }] }
      : { ...item, children: insertChapterNode(item.children, node, parentId) },
  );
}

export function updateChapterNodeInTree(
  nodes: ChapterNode[],
  patch: Partial<Pick<ChapterNode, "title" | "updated_at" | "word_count">> & {
    id?: string;
    chapter_id?: string | null;
  },
): ChapterNode[] {
  return nodes.map((node) => {
    const matchesId = patch.id ? node.id === patch.id : false;
    const matchesChapter = patch.chapter_id ? node.chapter_id === patch.chapter_id : false;
    if (matchesId || matchesChapter) {
      return {
        ...node,
        title: patch.title ?? node.title,
        updated_at: patch.updated_at ?? node.updated_at,
        word_count: patch.word_count ?? node.word_count,
      };
    }
    return { ...node, children: updateChapterNodeInTree(node.children, patch) };
  });
}

export function collectChapterIds(node: ChapterNode): Set<string> {
  const ids = new Set<string>();
  if (node.chapter_id) {
    ids.add(node.chapter_id);
  }
  node.children.forEach((child) => {
    collectChapterIds(child).forEach((id) => ids.add(id));
  });
  return ids;
}

export function summarizeChapterDelete(node: ChapterNode) {
  let folders = node.type === "folder" ? 1 : 0;
  let chapters = node.type === "chapter" ? 1 : 0;
  node.children.forEach((child) => {
    const childImpact = summarizeChapterDelete(child);
    folders += childImpact.folders;
    chapters += childImpact.chapters;
  });
  return { folders, chapters };
}

export function insertDocumentNode(
  nodes: DocumentNode[],
  node: DocumentNode,
  parentId: string | null,
): DocumentNode[] {
  if (!parentId) {
    return [...nodes, { ...node, children: node.children ?? [] }];
  }

  return nodes.map((item) =>
    item.id === parentId
      ? { ...item, children: [...item.children, { ...node, children: node.children ?? [] }] }
      : { ...item, children: insertDocumentNode(item.children, node, parentId) },
  );
}

export function updateDocumentNodeInTree(
  nodes: DocumentNode[],
  patch: Partial<Pick<DocumentNode, "title" | "updated_at">> & { id: string },
): DocumentNode[] {
  return nodes.map((node) =>
    node.id === patch.id
      ? {
          ...node,
          title: patch.title ?? node.title,
          updated_at: patch.updated_at ?? node.updated_at,
        }
      : { ...node, children: updateDocumentNodeInTree(node.children, patch) },
  );
}

export function collectDocumentIds(node: DocumentNode): Set<string> {
  const ids = new Set<string>();
  if (node.type === "markdown") {
    ids.add(node.id);
  }
  node.children.forEach((child) => {
    collectDocumentIds(child).forEach((id) => ids.add(id));
  });
  return ids;
}

export function summarizeDocumentDelete(node: DocumentNode) {
  let folders = node.type === "folder" ? 1 : 0;
  let documents = node.type === "markdown" ? 1 : 0;
  node.children.forEach((child) => {
    const childImpact = summarizeDocumentDelete(child);
    folders += childImpact.folders;
    documents += childImpact.documents;
  });
  return { folders, documents };
}
