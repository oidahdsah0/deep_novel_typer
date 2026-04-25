"use client";

import { ChatBotDialog } from "@/features/workspace/components/chat/ChatBotDialog";
import { VersionDialog } from "@/features/workspace/components/versions/VersionDialog";
import type { ChatSessionsApi } from "@/features/workspace/hooks/useChatSessions";
import type { VersionHistoryApi } from "@/features/workspace/hooks/useVersionHistory";
import type { ActiveResource } from "@/features/workspace/types";

type WorkspaceUtilityDialogsProps = {
  chat: ChatSessionsApi;
  resource: ActiveResource;
  versionHistory: VersionHistoryApi;
};

export function WorkspaceUtilityDialogs({
  chat,
  resource,
  versionHistory,
}: WorkspaceUtilityDialogsProps) {
  return (
    <>
      {versionHistory.isVersionDialogOpen ? (
        <VersionDialog
          draft={versionHistory.versionDraft}
          isLoading={versionHistory.isVersionLoading}
          onChangeDraft={versionHistory.setVersionDraft}
          onClose={() => versionHistory.setIsVersionDialogOpen(false)}
          onCreateManual={() => void versionHistory.handleCreateManualVersion()}
          onRestore={(version) => void versionHistory.handleRestoreVersion(version)}
          onSelectVersion={(version) => void versionHistory.handleSelectVersion(version)}
          resourceTitle={resource.title}
          selectedVersion={versionHistory.selectedVersion}
          versions={versionHistory.resourceVersions}
        />
      ) : null}
      {chat.isOpen ? (
        <ChatBotDialog
          activeSessionId={chat.activeSessionId}
          chapterId={resource.type === "chapter" ? resource.id : undefined}
          error={chat.error}
          isLoading={chat.isLoading}
          isSessionsLoading={chat.isSessionsLoading}
          messages={chat.messages}
          onClear={chat.clearMessages}
          onClose={chat.closeChat}
          onCreateSession={() => {
            chat.createSession();
          }}
          onDeleteSession={chat.removeSession}
          onRenameSession={chat.renameSession}
          onSelectSession={chat.selectSession}
          onSend={chat.sendMessage}
          sessions={chat.sessions}
        />
      ) : null}
    </>
  );
}
