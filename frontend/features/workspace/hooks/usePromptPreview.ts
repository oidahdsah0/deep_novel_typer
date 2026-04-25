"use client";

import { useState } from "react";
import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import {
  previewPrompt,
  type DraftGenerationAction,
  type GenerationPreset,
  type GenerationPresetKind,
  type GenerationPresetUpdate,
  type PromptPreviewInput,
  type PromptPreviewProfileOverride,
  type PromptPreviewResponse,
  type PromptRequestType,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import { useNotice } from "@/components/dialog";
import type {
  ActiveResource,
  ChapterSelection,
  DraftInsertionContext,
  PresetSaveState,
  PromptProfileDraft,
} from "../types";
import type { PromptPreviewApi } from "./workspaceInteractionApiTypes";

export type { PromptPreviewApi } from "./workspaceInteractionApiTypes";

function extractLastParagraph(value: string) {
  const paragraphs = value
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
  return paragraphs.at(-1) ?? "";
}

function pendingContent(
  pendingPresetPatches: MutableRefObject<Record<string, GenerationPresetUpdate>>,
  presetSaveKey: (kind: GenerationPresetKind, presetId: string) => string,
  kind: GenerationPresetKind,
  preset: GenerationPreset | undefined,
) {
  return preset
    ? pendingPresetPatches.current[presetSaveKey(kind, preset.id)]?.content ?? preset.content
    : "";
}

export function usePromptPreview({
  buildPromptProfileOverride,
  chapterSelection,
  content,
  documentSelection,
  pendingPresetPatches,
  presetSaveKey,
  projectId,
  promptDraft,
  readDraftInsertionContext,
  resource,
  saveActive,
  flushChapterWritingSynopsis,
  selectedAuthorPreset,
  selectedChapterBlueprintPreset,
  selectedDocumentGenerationPreset,
  selectedDocumentPolishPreset,
  selectedEditorPreset,
  selectedPolishPreset,
  selectedWritingPreset,
  setPromptSaveState,
  workspace,
}: {
  buildPromptProfileOverride: (
    draft: PromptProfileDraft,
  ) => PromptPreviewProfileOverride | null;
  chapterSelection: ChapterSelection | null;
  content: string;
  documentSelection: ChapterSelection | null;
  pendingPresetPatches: MutableRefObject<Record<string, GenerationPresetUpdate>>;
  presetSaveKey: (kind: GenerationPresetKind, presetId: string) => string;
  projectId: string;
  promptDraft: PromptProfileDraft | null;
  readDraftInsertionContext: () => DraftInsertionContext;
  resource: ActiveResource;
  saveActive: (nextContent?: string) => Promise<void>;
  flushChapterWritingSynopsis: () => Promise<void>;
  selectedAuthorPreset: GenerationPreset | undefined;
  selectedChapterBlueprintPreset: GenerationPreset | undefined;
  selectedDocumentGenerationPreset: GenerationPreset | undefined;
  selectedDocumentPolishPreset: GenerationPreset | undefined;
  selectedEditorPreset: GenerationPreset | undefined;
  selectedPolishPreset: GenerationPreset | undefined;
  selectedWritingPreset: GenerationPreset | undefined;
  setPromptSaveState: Dispatch<SetStateAction<PresetSaveState>>;
  workspace: WorkspaceSnapshot;
}) {
  const [promptPreview, setPromptPreview] = useState<PromptPreviewResponse | null>(null);
  const [isPromptPreviewLoading, setIsPromptPreviewLoading] = useState(false);
  const notice = useNotice();

  function buildPromptPreviewInput(
    requestType: PromptRequestType,
    profileOverride: PromptPreviewProfileOverride | null = null,
    draftAnchorOverride: DraftInsertionContext | null = null,
  ): PromptPreviewInput {
    const chapterId = resource.type === "chapter" ? resource.id : workspace.active_chapter.id;
    const chapterContent =
      resource.type === "chapter" ? content : workspace.active_chapter.content;
    const documentId = resource.type === "document" ? resource.id : null;
    const draftAnchor =
      requestType === "quick_generate_next_paragraph" ||
      requestType === "generate_chapter_blueprint" ||
      requestType === "generate_next_paragraph" ||
      requestType === "generate_next_section"
        ? (draftAnchorOverride ?? readDraftInsertionContext())
        : null;

    return {
      request_type: requestType,
      chapter_id: chapterId,
      document_id: documentId,
      paragraph: extractLastParagraph(chapterContent),
      cursor_index: draftAnchor?.cursorIndex,
      previous_paragraph: draftAnchor?.previousParagraph,
      next_paragraph: draftAnchor?.nextParagraph,
      selected_text:
        requestType === "polish_document_selection"
          ? documentSelection?.text ?? ""
          : chapterSelection?.text ?? "",
      writing_prompt: pendingContent(
        pendingPresetPatches,
        presetSaveKey,
        "writing_mode",
        selectedWritingPreset,
      ),
      quick_prompt: "",
      blueprint_prompt: pendingContent(
        pendingPresetPatches,
        presetSaveKey,
        "chapter_blueprint_mode",
        selectedChapterBlueprintPreset,
      ),
      author_persona: pendingContent(
        pendingPresetPatches,
        presetSaveKey,
        "author_persona",
        selectedAuthorPreset,
      ),
      author_persona_id: selectedAuthorPreset?.id ?? "",
      author_persona_name: selectedAuthorPreset?.name ?? "",
      polish_prompt:
        requestType === "polish_document_selection"
          ? pendingContent(
              pendingPresetPatches,
              presetSaveKey,
              "document_polish_mode",
              selectedDocumentPolishPreset,
            )
          : pendingContent(
              pendingPresetPatches,
              presetSaveKey,
              "polish_mode",
              selectedPolishPreset,
            ),
      generation_prompt: pendingContent(
        pendingPresetPatches,
        presetSaveKey,
        "document_generation_mode",
        selectedDocumentGenerationPreset,
      ),
      editor_persona: pendingContent(
        pendingPresetPatches,
        presetSaveKey,
        "editor_persona",
        selectedEditorPreset,
      ),
      editor_persona_id: selectedEditorPreset?.id ?? "",
      editor_persona_name: selectedEditorPreset?.name ?? "",
      profile_override: profileOverride,
    };
  }

  async function handlePreviewPrompt(
    requestType: PromptRequestType,
    profileOverride: PromptPreviewProfileOverride | null = null,
    draftAnchorOverride: DraftInsertionContext | null = null,
  ) {
    setIsPromptPreviewLoading(true);
    try {
      await Promise.all([saveActive(content), flushChapterWritingSynopsis()]);
      const preview = await previewPrompt(
        projectId,
        buildPromptPreviewInput(requestType, profileOverride, draftAnchorOverride),
      );
      setPromptPreview(preview);
    } catch (error) {
      void notice(error instanceof Error ? error.message : "请求预览失败", {
        title: "请求预览失败",
      });
    } finally {
      setIsPromptPreviewLoading(false);
    }
  }

  function handlePreviewPromptManager() {
    if (!promptDraft) {
      return;
    }
    const profileOverride = buildPromptProfileOverride(promptDraft);
    if (!profileOverride) {
      setPromptSaveState("error");
      return;
    }
    void handlePreviewPrompt(promptDraft.request_type, profileOverride);
  }

  function handlePreviewDraftGeneration(
    action: DraftGenerationAction,
    draftAnchorOverride: DraftInsertionContext | null = null,
  ) {
    return handlePreviewPrompt(
      action === "next_paragraph" ? "generate_next_paragraph" : "generate_next_section",
      null,
      draftAnchorOverride,
    );
  }

  return {
    handlePreviewDraftGeneration,
    handlePreviewPrompt,
    handlePreviewPromptManager,
    isPromptPreviewLoading,
    promptPreview,
    setPromptPreview,
  } satisfies PromptPreviewApi;
}
