import type { Dispatch, SetStateAction, TransitionStartFunction } from "react";

import {
  exportProjectArchive,
  getLibrarySnapshot,
  importProjectArchive,
  type LibrarySnapshot,
  type ProjectImportResponse,
  type ProjectSummary,
} from "@/lib/api/index";
import { useConfirm } from "@/components/dialog";

export function useProjectTransfer({
  setLibrary,
  setSelectedId,
  setTransferNotice,
  startTransition,
}: {
  setLibrary: Dispatch<SetStateAction<LibrarySnapshot>>;
  setSelectedId: Dispatch<SetStateAction<string>>;
  setTransferNotice: Dispatch<SetStateAction<string>>;
  startTransition: TransitionStartFunction;
}) {
  const confirm = useConfirm();

  async function handleExport(project: ProjectSummary) {
    if (
      !(await confirm(`确认导出「${project.title}」的完整项目备份？`, {
        confirmLabel: "导出",
      }))
    ) {
      return;
    }

    const filename = `${project.id}-deep-novel-export.zip`;
    let directory: DirectoryPickerResult;
    try {
      directory = await chooseExportDirectory();
    } catch (error) {
      setTransferNotice(`目录选择失败：${errorMessage(error)}`);
      return;
    }
    if (directory.cancelled) {
      return;
    }
    startTransition(async () => {
      try {
        const archive = await exportProjectArchive(project.id);
        if (directory.handle) {
          await writeArchiveToDirectory(directory.handle, archive, filename);
          setTransferNotice(`已导出「${project.title}」到「${directory.handle.name}」。`);
          return;
        }
        downloadArchive(archive, filename);
        setTransferNotice(
          `当前浏览器不支持目录选择，已导出「${project.title}」到默认下载位置。`,
        );
      } catch (error) {
        setTransferNotice(`导出失败：${errorMessage(error)}`);
      }
    });
  }

  async function handleImport(file: File | null) {
    if (!file) {
      return;
    }
    if (
      !(await confirm("导入会创建一个新的小说项目，不会覆盖现有项目。确认导入？", {
        confirmLabel: "导入",
      }))
    ) {
      return;
    }
    startTransition(async () => {
      setTransferNotice(`正在导入「${file.name}」...`);
      let result: ProjectImportResponse;
      try {
        result = await importProjectArchive(file);
      } catch (error) {
        setTransferNotice(`导入失败：${errorMessage(error)}`);
        return;
      }

      let snapshot: LibrarySnapshot;
      try {
        snapshot = await getLibrarySnapshot();
      } catch (error) {
        setTransferNotice(`导入已完成，但刷新项目列表失败：${errorMessage(error)}`);
        return;
      }

      setLibrary(snapshot);
      setSelectedId(result.imported_project_id);
      setTransferNotice(importNotice(result));
    });
  }

  return {
    handleExport,
    handleImport,
  };
}

type DirectoryHandle = {
  name: string;
  getFileHandle: (
    name: string,
    options?: { create?: boolean },
  ) => Promise<{
    createWritable: () => Promise<{
      close: () => Promise<void>;
      write: (data: Blob) => Promise<void>;
    }>;
  }>;
};

type DirectoryPickerResult =
  | { cancelled: true; handle: null }
  | { cancelled: false; handle: DirectoryHandle | null };

async function chooseExportDirectory(): Promise<DirectoryPickerResult> {
  const picker = (window as Window & {
    showDirectoryPicker?: (options?: {
      id?: string;
      mode?: "read" | "readwrite";
      startIn?: "desktop" | "documents" | "downloads";
    }) => Promise<DirectoryHandle>;
  }).showDirectoryPicker;

  if (!picker) {
    return { cancelled: false, handle: null };
  }

  try {
    const handle = await picker({
      id: "deep-novel-exports",
      mode: "readwrite",
      startIn: "documents",
    });
    return { cancelled: false, handle };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return { cancelled: true, handle: null };
    }
    throw error;
  }
}

async function writeArchiveToDirectory(
  directory: DirectoryHandle,
  archive: Blob,
  filename: string,
) {
  const fileHandle = await directory.getFileHandle(filename, { create: true });
  const writable = await fileHandle.createWritable();
  try {
    await writable.write(archive);
  } finally {
    await writable.close();
  }
}

function downloadArchive(archive: Blob, filename: string) {
  const url = URL.createObjectURL(archive);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function importNotice(result: ProjectImportResponse) {
  const warningText = result.warnings.length ? ` ${result.warnings.join(" ")}` : "";
  return `已导入「${result.project.title}」。${warningText}`;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "未知错误";
}
