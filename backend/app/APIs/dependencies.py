from __future__ import annotations

from app.Services.api_configs import APIConfigService, OpenAIAPIConfigHealthChecker
from app.Services.chapter_docx_export_service import ChapterDocxExportService
from app.Services.chapter_service import ChapterService
from app.Services.chat_service import ChatService
from app.Services.chat_session import ChatSessionRepository
from app.Services.debug_log_service import DebugLogService
from app.Services.document_service import DocumentService
from app.Services.embeddings import EmbeddingService, OpenAIEmbeddingRuntime
from app.Services.generation_service import GenerationService
from app.Services.library_service import LibraryService
from app.Services.perspective_service import PerspectiveService
from app.Services.prompt_preview_service import PromptPreviewService
from app.Services.prompt_profiles import PromptProfileService
from app.Services.project_transfer import ProjectTransferService
from app.Services.project_service import ProjectService
from app.Services.search import ProjectSearchService
from app.Services.model_request_queue_service import (
  ModelRequestQueueService,
  QueuedCompletionClient,
)
from app.Services.suggestion_queue_service import SuggestionQueueService
from app.Services.suggestion_service import SuggestionService
from app.Services.typewriter_layout import TypewriterLayoutService
from app.Services.version_service import VersionService
from app.Services.workspace_service import WorkspaceService
from app.Utils.config import get_settings
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Utils.llm import OpenAIChatClient
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore

settings = get_settings()
path_resolver = PathResolver(settings.data_dir, settings.trash_dir)
lock_registry = AsyncLockRegistry()
file_store = AsyncFileStore(settings.data_dir, settings.thread_pool_workers)
database = AsyncDatabase(settings.db_path)
model_request_queue_service = ModelRequestQueueService()
raw_llm_client = OpenAIChatClient(
  api_key=settings.llm.api_key,
  api_key_required=settings.llm.api_key_required,
  enabled=settings.llm.enabled,
  base_url=settings.llm.base_url,
  headers=settings.llm.headers,
  mode=settings.llm.mode,
  model=settings.llm.model,
  non_stream_request_options=settings.llm.non_stream_request_options,
  timeout_seconds=settings.llm.timeout_seconds,
)
llm_client = QueuedCompletionClient(raw_llm_client, model_request_queue_service)

project_service = ProjectService(database, file_store, path_resolver, lock_registry)
project_transfer_service = ProjectTransferService(
  database, file_store, path_resolver, lock_registry
)
project_search_service = ProjectSearchService(
  database,
  file_store,
  path_resolver,
  project_service,
  settings.generation.presets,
)
api_config_service = APIConfigService(
  database,
  lock_registry,
  settings.llm,
  OpenAIAPIConfigHealthChecker(
    headers=settings.llm.headers,
    timeout_seconds=settings.llm.timeout_seconds,
    request_queue=model_request_queue_service,
  ),
)
debug_log_service = DebugLogService(database, lock_registry)
typewriter_layout_service = TypewriterLayoutService(database, lock_registry)
chapter_service = ChapterService(
  database, file_store, path_resolver, lock_registry, project_service
)
chapter_docx_export_service = ChapterDocxExportService(project_service, chapter_service)
document_service = DocumentService(
  database, file_store, path_resolver, lock_registry, project_service
)
embedding_service = EmbeddingService(
  database,
  lock_registry,
  project_service,
  chapter_service,
  document_service,
  api_config_service,
  OpenAIEmbeddingRuntime(
    model_request_queue_service,
    headers=settings.llm.headers,
    timeout_seconds=settings.llm.timeout_seconds,
  ),
  chroma_path=settings.data_dir / "chroma",
  debug_log_service=debug_log_service,
)
perspective_service = PerspectiveService(database, lock_registry, project_service)
prompt_profile_service = PromptProfileService(
  database,
  lock_registry,
  project_service,
  chapter_service,
  document_service,
)
suggestion_service = SuggestionService(
  chapter_service,
  perspective_service,
  project_service,
  prompt_profile_service,
  api_config_service,
  llm_client,
  debug_log_service,
)
suggestion_queue_service = SuggestionQueueService(suggestion_service)
generation_service = GenerationService(
  database,
  lock_registry,
  project_service,
  chapter_service,
  document_service,
  prompt_profile_service,
  api_config_service,
  llm_client,
  settings.generation.presets,
  debug_log_service,
)
prompt_preview_service = PromptPreviewService(
  project_service,
  chapter_service,
  document_service,
  perspective_service,
  prompt_profile_service,
  api_config_service,
)
chat_session_repo = ChatSessionRepository(database)

chat_service = ChatService(
  project_service,
  chapter_service,
  document_service,
  prompt_profile_service,
  api_config_service,
  llm_client,
  debug_log_service,
  chat_session_repo=chat_session_repo,
  locks=lock_registry,
)
version_service = VersionService(
  database,
  file_store,
  path_resolver,
  lock_registry,
  project_service,
  chapter_service,
  document_service,
)
library_service = LibraryService(database, project_service, api_config_service, version_service)
workspace_service = WorkspaceService(
  project_service,
  chapter_service,
  document_service,
  perspective_service,
  api_config_service,
  suggestion_service,
  generation_service,
  prompt_profile_service,
  typewriter_layout_service,
)


def get_database() -> AsyncDatabase:
  return database


def get_project_service() -> ProjectService:
  return project_service


def get_project_transfer_service() -> ProjectTransferService:
  return project_transfer_service


def get_project_search_service() -> ProjectSearchService:
  return project_search_service


def get_library_service() -> LibraryService:
  return library_service


def get_api_config_service() -> APIConfigService:
  return api_config_service


def get_model_request_queue_service() -> ModelRequestQueueService:
  return model_request_queue_service


def get_debug_log_service() -> DebugLogService:
  return debug_log_service


def get_typewriter_layout_service() -> TypewriterLayoutService:
  return typewriter_layout_service


def get_embedding_service() -> EmbeddingService:
  return embedding_service


def get_chapter_service() -> ChapterService:
  return chapter_service


def get_chapter_docx_export_service() -> ChapterDocxExportService:
  return chapter_docx_export_service


def get_document_service() -> DocumentService:
  return document_service


def get_perspective_service() -> PerspectiveService:
  return perspective_service


def get_prompt_profile_service() -> PromptProfileService:
  return prompt_profile_service


def get_prompt_preview_service() -> PromptPreviewService:
  return prompt_preview_service


def get_suggestion_service() -> SuggestionService:
  return suggestion_service


def get_suggestion_queue_service() -> SuggestionQueueService:
  return suggestion_queue_service


def get_generation_service() -> GenerationService:
  return generation_service


def get_version_service() -> VersionService:
  return version_service


def get_chat_service() -> ChatService:
  return chat_service


def get_workspace_service() -> WorkspaceService:
  return workspace_service
