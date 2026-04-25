import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import type {
  GenerationPreset,
  GenerationPresetKind,
  GenerationPresetUpdate,
} from "@/lib/api/index";
import type {
  ActiveResource,
  ChapterSelection,
  DraftInsertionContext,
  FloatingMenuPosition,
} from "../../types";

export type DraftGenerationParams = {
  authorPresets: GenerationPreset[];
  chapterBlueprintPresets: GenerationPreset[];
  chapterSelection: ChapterSelection | null;
  commitGeneratedContent: (nextContent: string) => void;
  content: string;
  flushPresetSave: (kind: GenerationPresetKind, presetId: string) => Promise<void>;
  flushChapterWritingSynopsis: () => Promise<void>;
  pendingPresetPatches: MutableRefObject<Record<string, GenerationPresetUpdate>>;
  onPolishAccepted: (start: number, end: number) => void;
  polishPresets: GenerationPreset[];
  quickGenerationPresets: GenerationPreset[];
  presetSaveKey: (kind: GenerationPresetKind, presetId: string) => string;
  projectId: string;
  readDraftInsertionContext: () => DraftInsertionContext;
  readChapterSelection: () => ChapterSelection | null;
  resource: ActiveResource;
  saveActive: (nextContent?: string) => Promise<void>;
  selectedAuthorPreset: GenerationPreset | undefined;
  selectedChapterBlueprintPreset: GenerationPreset | undefined;
  selectedPolishPreset: GenerationPreset | undefined;
  selectedQuickGenerationPreset: GenerationPreset | undefined;
  selectedWritingPreset: GenerationPreset | undefined;
  setChapterSelection: Dispatch<SetStateAction<ChapterSelection | null>>;
  setContent: Dispatch<SetStateAction<string>>;
  setSelectedAuthorPresetId: Dispatch<SetStateAction<string>>;
  setSelectedChapterBlueprintPresetId: Dispatch<SetStateAction<string>>;
  setSelectedPolishPresetId: Dispatch<SetStateAction<string>>;
  setSelectedQuickGenerationPresetId: Dispatch<SetStateAction<string>>;
  setSelectedWritingPresetId: Dispatch<SetStateAction<string>>;
  setSelectionMenuPosition: Dispatch<SetStateAction<FloatingMenuPosition>>;
  writingPresets: GenerationPreset[];
};
