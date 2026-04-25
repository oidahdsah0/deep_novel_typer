from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.debug_log_service import DebugLogService
from app.Services.document_service import DocumentService
from app.Services.generation_service import GenerationService
from app.Services.perspective_service import PerspectiveService
from app.Services.prompt_preview_service import PromptPreviewService
from app.Services.prompt_profiles import PromptProfileService
from app.Services.project_service import ProjectService
from app.Services.suggestion_service import SuggestionService
from app.Services.version_service import VersionService
from app.Utils.config import _load_llm_settings
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from tests.fakes import GENERATION_DEFAULTS


async def build_services(tmp_path):
  projects_dir = tmp_path / "projects"
  trash_dir = tmp_path / "trash"
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  store = AsyncFileStore(projects_dir, max_workers=2)
  paths = PathResolver(projects_dir, trash_dir)
  locks = AsyncLockRegistry()
  project_service = ProjectService(db, store, paths, locks)
  chapter_service = ChapterService(db, store, paths, locks, project_service)
  document_service = DocumentService(db, store, paths, locks, project_service)
  return store, project_service, chapter_service, document_service


async def build_version_services(tmp_path):
  projects_dir = tmp_path / "projects"
  trash_dir = tmp_path / "trash"
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  store = AsyncFileStore(projects_dir, max_workers=2)
  paths = PathResolver(projects_dir, trash_dir)
  locks = AsyncLockRegistry()
  project_service = ProjectService(db, store, paths, locks)
  chapter_service = ChapterService(db, store, paths, locks, project_service)
  document_service = DocumentService(db, store, paths, locks, project_service)
  version_service = VersionService(
    db,
    store,
    paths,
    locks,
    project_service,
    chapter_service,
    document_service,
  )
  return store, project_service, chapter_service, document_service, version_service


async def build_suggestion_services(tmp_path, llm_client):
  projects_dir = tmp_path / "projects"
  trash_dir = tmp_path / "trash"
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  store = AsyncFileStore(projects_dir, max_workers=2)
  paths = PathResolver(projects_dir, trash_dir)
  locks = AsyncLockRegistry()
  project_service = ProjectService(db, store, paths, locks)
  chapter_service = ChapterService(db, store, paths, locks, project_service)
  document_service = DocumentService(db, store, paths, locks, project_service)
  perspective_service = PerspectiveService(db, locks, project_service)
  api_config_service = APIConfigService(db, locks, _load_llm_settings())
  prompt_profile_service = PromptProfileService(
    db,
    locks,
    project_service,
    chapter_service,
    document_service,
  )
  await api_config_service.ensure_default_config()
  suggestion_service = SuggestionService(
    chapter_service,
    perspective_service,
    project_service,
    prompt_profile_service,
    api_config_service,
    llm_client,
  )
  return (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  )


async def build_generation_services(
  tmp_path,
  llm_client,
  *,
  include_prompt_profile_service=False,
  include_debug_log_service=False,
  include_document_service=False,
  include_prompt_preview_service=False,
):
  projects_dir = tmp_path / "projects"
  trash_dir = tmp_path / "trash"
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  store = AsyncFileStore(projects_dir, max_workers=2)
  paths = PathResolver(projects_dir, trash_dir)
  locks = AsyncLockRegistry()
  project_service = ProjectService(db, store, paths, locks)
  chapter_service = ChapterService(db, store, paths, locks, project_service)
  document_service = DocumentService(db, store, paths, locks, project_service)
  prompt_profile_service = PromptProfileService(
    db,
    locks,
    project_service,
    chapter_service,
    document_service,
  )
  debug_log_service = DebugLogService(db, locks)
  api_config_service = APIConfigService(db, locks, _load_llm_settings())
  await api_config_service.ensure_default_config()
  generation_service = GenerationService(
    db,
    locks,
    project_service,
    chapter_service,
    document_service,
    prompt_profile_service,
    api_config_service,
    llm_client,
    GENERATION_DEFAULTS,
    debug_log_service,
  )
  prompt_preview_service = PromptPreviewService(
    project_service,
    chapter_service,
    document_service,
    PerspectiveService(db, locks, project_service),
    prompt_profile_service,
    api_config_service,
  )
  result = [
    store,
    project_service,
    chapter_service,
    generation_service,
    api_config_service,
  ]
  if include_document_service:
    result.append(document_service)
  if include_prompt_preview_service:
    result.append(prompt_preview_service)
  if include_prompt_profile_service:
    result.append(prompt_profile_service)
  if include_debug_log_service:
    result.append(debug_log_service)
  return tuple(result)
