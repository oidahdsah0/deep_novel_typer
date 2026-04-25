"use client";

import { useEffect, useMemo, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  updateVersionSettings,
  type ApiConfigHealthCheckResult,
  type ApiConfigInput,
  type LibrarySnapshot,
  type ProjectInput,
  type ProjectStatus,
  type VersionSettings,
} from "@/lib/api/index";
import type { LibraryPanel } from "@/features/library/types";
import {
  emptyDraft,
  normalizeLibrarySnapshot,
  normalizeVersionSettings,
  templateToApiConfigInput,
  toApiConfigInput,
} from "@/features/library/utils";
import { useApiConfigActions } from "@/features/library/hooks/useApiConfigActions";
import { useLibraryLayout } from "@/features/library/hooks/useLibraryLayout";
import { useProjectActions } from "@/features/library/hooks/useProjectActions";
import { useProjectTransfer } from "@/features/library/hooks/useProjectTransfer";
import { APIConfigCreateDialog } from "@/features/library/components/APIConfigCreateDialog";
import { APIConfigDetail } from "@/features/library/components/APIConfigDetail";
import { LibraryHeader } from "@/features/library/components/LibraryHeader";
import { LibrarySidebar } from "@/features/library/components/LibrarySidebar";
import { ProjectCreateDialog } from "@/features/library/components/ProjectCreateDialog";
import { ProjectDetail } from "@/features/library/components/ProjectDetail";
import { APIConfigList } from "@/features/library/components/api-configs/APIConfigList";
import { ProjectList } from "@/features/library/components/projects/ProjectList";
import {
  readTabQuickGenerationEnabled,
  writeTabQuickGenerationEnabled,
} from "@/features/workspace/shortcutSettings";
import {
  ShortcutSettingsDetail,
  ShortcutSettingsOverview,
} from "@/features/library/components/ShortcutSettingsPanel";
import {
  VersionSettingsDetail,
  VersionSettingsOverview,
} from "@/features/library/components/VersionSettingsPanel";

export function LibraryClient({ initialLibrary }: { initialLibrary: LibrarySnapshot }) {
  const initialSnapshot = normalizeLibrarySnapshot(initialLibrary);
  const router = useRouter();
  const [library, setLibrary] = useState(initialSnapshot);
  const [activePanel, setActivePanel] = useState<LibraryPanel>("projects");
  const [selectedId, setSelectedId] = useState(initialSnapshot.projects[0]?.id ?? "");
  const [selectedConfigId, setSelectedConfigId] = useState(initialSnapshot.api_configs[0]?.id ?? "");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | "all">("all");
  const [draft, setDraft] = useState<ProjectInput>(emptyDraft);
  const [editDraft, setEditDraft] = useState<Partial<ProjectInput>>({});
  const [apiDraft, setApiDraft] = useState<ApiConfigInput>(() =>
    templateToApiConfigInput(initialSnapshot.api_config_templates[0]),
  );
  const [apiEditDraft, setApiEditDraft] = useState<ApiConfigInput | null>(null);
  const [isProjectCreateDialogOpen, setIsProjectCreateDialogOpen] = useState(false);
  const [isApiConfigCreateDialogOpen, setIsApiConfigCreateDialogOpen] = useState(false);
  const [apiHealthResults, setApiHealthResults] = useState<
    Record<string, ApiConfigHealthCheckResult>
  >({});
  const [checkingApiConfigId, setCheckingApiConfigId] = useState<string | null>(null);
  const [transferNotice, setTransferNotice] = useState("");
  const [versionSettingsDraft, setVersionSettingsDraft] = useState<VersionSettings>(initialSnapshot.version_settings);
  const [tabQuickGenerationEnabled, setTabQuickGenerationEnabled] = useState(false);
  const importInputRef = useRef<HTMLInputElement>(null);
  const [isPending, startTransition] = useTransition();
  const {
    handleLibraryDetailResizePointerDown,
    isLibraryDetailVisible,
    isLibrarySidebarVisible,
    libraryClassName,
    libraryStyle,
    setIsLibraryDetailVisible,
    setIsLibrarySidebarVisible,
  } = useLibraryLayout();

  useEffect(() => {
    setTabQuickGenerationEnabled(readTabQuickGenerationEnabled());
  }, []);

  const selectedProject = library.projects.find((project) => project.id === selectedId);
  const selectedConfig = library.api_configs.find((config) => config.id === selectedConfigId);
  const selectedConfigKindCount = selectedConfig
    ? library.api_configs.filter((config) => config.kind === selectedConfig.kind).length
    : 0;
  const selectedConfigDraft = selectedConfig
    ? (apiEditDraft ?? toApiConfigInput(selectedConfig))
    : null;
  const templates = library.api_config_templates;

  const visibleProjects = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return library.projects.filter((project) => {
      const matchesStatus = statusFilter === "all" || project.status === statusFilter;
      const haystack = [
        project.title,
        project.subtitle,
        project.description,
        project.genre,
      ].join(" ").toLowerCase();
      return matchesStatus && (!normalizedQuery || haystack.includes(normalizedQuery));
    });
  }, [library.projects, query, statusFilter]);

  const { handleCreate, handleDelete, handleOpen, handleUpdate } = useProjectActions({
    draft,
    editDraft,
    library,
    navigateToProject: (projectId) => router.push(`/projects/${projectId}`),
    selectedProject,
    setDraft,
    setEditDraft,
    setLibrary,
    setSelectedId,
    onProjectCreated: () => setIsProjectCreateDialogOpen(false),
    startTransition,
  });
  const { handleExport, handleImport } = useProjectTransfer({
    setLibrary,
    setSelectedId,
    setTransferNotice,
    startTransition,
  });
  const {
    handleCheckApiConfig,
    handleCreateApiConfig,
    handleDeleteApiConfig,
    handleSetDefaultApiConfig,
    handleUpdateApiConfig,
  } = useApiConfigActions({
    apiDraft,
    library,
    selectedConfig,
    selectedConfigDraft,
    setApiDraft,
    setApiEditDraft,
    setApiHealthResults,
    setCheckingApiConfigId,
    setLibrary,
    setSelectedConfigId,
    onApiConfigCreated: () => setIsApiConfigCreateDialogOpen(false),
    startTransition,
    templates,
  });

  function handleOpenApiConfigCreateDialog() {
    setApiDraft(templateToApiConfigInput(templates[0]));
    setIsApiConfigCreateDialogOpen(true);
  }

  function handleOpenProjectCreateDialog() {
    setDraft(emptyDraft);
    setIsProjectCreateDialogOpen(true);
  }

  function handleUpdateVersionSettings() {
    startTransition(async () => {
      const updated = await updateVersionSettings(normalizeVersionSettings(versionSettingsDraft));
      setLibrary((current) => ({ ...current, version_settings: updated }));
      setVersionSettingsDraft(updated);
    });
  }

  function handleChangeTabQuickGeneration(enabled: boolean) {
    setTabQuickGenerationEnabled(enabled);
    writeTabQuickGenerationEnabled(enabled);
  }

  return (
    <main className={libraryClassName} style={libraryStyle}>
      {isLibrarySidebarVisible ? (
        <LibrarySidebar
          activePanel={activePanel}
          library={library}
          onOpenApiConfigCreate={handleOpenApiConfigCreateDialog}
          onOpenProjectCreate={handleOpenProjectCreateDialog}
          query={query}
          setActivePanel={setActivePanel}
          setQuery={setQuery}
          setStatusFilter={setStatusFilter}
          statusFilter={statusFilter}
        />
      ) : null}

      <section
        className="library-main"
        aria-label={
          activePanel === "projects"
            ? "小说项目列表"
            : activePanel === "api-configs"
              ? "API 配置列表"
              : activePanel === "save-settings"
                ? "保存机制设置"
                : "快捷键设置"
        }
      >
        <LibraryHeader
          activePanel={activePanel}
          importInputRef={importInputRef}
          isDetailVisible={isLibraryDetailVisible}
          isPending={isPending}
          isSidebarVisible={isLibrarySidebarVisible}
          onDebugOpen={() => router.push("/debug")}
          onImport={handleImport}
          onToggleDetail={() => setIsLibraryDetailVisible((current) => !current)}
          onToggleSidebar={() => setIsLibrarySidebarVisible((current) => !current)}
        />

        {activePanel === "projects" ? (
          <ProjectList
            onDelete={handleDelete}
            onExport={handleExport}
            onOpen={handleOpen}
            onSelect={setSelectedId}
            projects={visibleProjects}
            selectedId={selectedId}
          />
        ) : activePanel === "api-configs" ? (
          <APIConfigList
            checkingApiConfigId={checkingApiConfigId}
            configs={library.api_configs}
            healthResults={apiHealthResults}
            onHealthCheck={(config) => void handleCheckApiConfig(config)}
            onSelect={(configId) => {
              setSelectedConfigId(configId);
              setApiEditDraft(null);
            }}
            selectedConfigId={selectedConfigId}
            templates={templates}
          />
        ) : activePanel === "save-settings" ? (
          <VersionSettingsOverview settings={versionSettingsDraft} />
        ) : (
          <ShortcutSettingsOverview tabQuickGenerationEnabled={tabQuickGenerationEnabled} />
        )}
      </section>

      {isLibraryDetailVisible ? (
        <aside className="project-detail" aria-label="项目详情">
          <button
            className="rail-resize-handle rail-resize-handle-left"
            onPointerDown={handleLibraryDetailResizePointerDown}
            type="button"
            aria-label="拖拽调整右侧栏宽度"
          />
          {activePanel === "projects" ? (
            <ProjectDetail
              editDraft={editDraft}
              onChange={setEditDraft}
              onDelete={selectedProject ? () => handleDelete(selectedProject) : () => undefined}
              onExport={selectedProject ? () => handleExport(selectedProject) : () => undefined}
              onOpen={selectedProject ? () => handleOpen(selectedProject) : () => undefined}
              onSave={handleUpdate}
              project={selectedProject}
            />
          ) : activePanel === "api-configs" ? (
            <APIConfigDetail
              draft={selectedConfigDraft}
              healthResult={selectedConfig ? apiHealthResults[selectedConfig.id] : undefined}
              isCheckingHealth={selectedConfig ? checkingApiConfigId === selectedConfig.id : false}
              isOnlyKindConfig={!selectedConfig || selectedConfigKindCount <= 1}
              onChange={setApiEditDraft}
              onDelete={selectedConfig ? () => handleDeleteApiConfig(selectedConfig) : undefined}
              onHealthCheck={
                selectedConfig ? () => void handleCheckApiConfig(selectedConfig) : undefined
              }
              onSave={handleUpdateApiConfig}
              onSetDefault={
                selectedConfig && !selectedConfig.is_default
                  ? () => handleSetDefaultApiConfig(selectedConfig)
                  : undefined
              }
              selectedConfig={selectedConfig}
              templates={templates}
            />
          ) : activePanel === "save-settings" ? (
            <VersionSettingsDetail
              onChange={setVersionSettingsDraft}
              onSave={handleUpdateVersionSettings}
              settings={versionSettingsDraft}
            />
          ) : (
            <ShortcutSettingsDetail
              onChange={handleChangeTabQuickGeneration}
              tabQuickGenerationEnabled={tabQuickGenerationEnabled}
            />
          )}

        </aside>
      ) : null}
      {isProjectCreateDialogOpen ? (
        <ProjectCreateDialog
          draft={draft}
          onChange={setDraft}
          onClose={() => setIsProjectCreateDialogOpen(false)}
          onCreate={handleCreate}
        />
      ) : null}
      {isApiConfigCreateDialogOpen ? (
        <APIConfigCreateDialog
          draft={apiDraft}
          onChange={setApiDraft}
          onClose={() => setIsApiConfigCreateDialogOpen(false)}
          onCreate={handleCreateApiConfig}
          templates={templates}
        />
      ) : null}
      {transferNotice ? <div className="library-transfer-notice">{transferNotice}</div> : null}
    </main>
  );
}
