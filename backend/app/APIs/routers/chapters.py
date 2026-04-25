from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Response, status

from app.APIs.dependencies import (
  get_chapter_docx_export_service,
  get_chapter_service,
  get_project_service,
  get_version_service,
)
from app.Services.chapter_docx_export_service import (
  DOCX_MEDIA_TYPE,
  ChapterDocxExportService,
)
from app.Services.chapter_service import ChapterService
from app.Services.project_service import ProjectService
from app.Services.version_service import VersionService
from app.Schemas.chapters import (
  ChapterDetail,
  ChapterNode,
  ChapterSearchResponse,
  ChapterSummary,
  CreateChapterNodeRequest,
  CreateChapterRequest,
  ExportChaptersDocxRequest,
  MoveChapterNodeRequest,
  MoveChapterNodeResponse,
  UpdateChapterNodeRequest,
  UpdateChapterWritingSynopsisRequest,
  UpdateChapterRequest,
)
from app.Schemas.resource_saves import (
  ChapterSaveResponse,
  ChapterWritingSynopsisSaveResponse,
)

router = APIRouter()


@router.get("", response_model=list[ChapterSummary])
async def list_chapters(
  project_id: str,
  service: ChapterService = Depends(get_chapter_service),
) -> list[ChapterSummary]:
  return await service.list_chapters(project_id)


@router.get("/tree", response_model=list[ChapterNode])
async def list_chapter_tree(
  project_id: str,
  service: ChapterService = Depends(get_chapter_service),
) -> list[ChapterNode]:
  return await service.list_chapter_tree(project_id)


@router.get("/search", response_model=ChapterSearchResponse)
async def search_chapters(
  project_id: str,
  q: str = Query(default="", max_length=120),
  scope_node_id: str | None = Query(default=None, max_length=120),
  limit: int = Query(default=30, ge=1, le=50),
  service: ChapterService = Depends(get_chapter_service),
) -> ChapterSearchResponse:
  return await service.search_chapters(
    project_id,
    query=q,
    scope_node_id=scope_node_id,
    limit=limit,
  )


@router.post("/export-docx")
async def export_chapters_docx(
  project_id: str,
  request: ExportChaptersDocxRequest,
  service: ChapterDocxExportService = Depends(get_chapter_docx_export_service),
) -> Response:
  document = await service.export_chapters(project_id, request)
  filename = quote(document.filename)
  return Response(
    content=document.content,
    media_type=DOCX_MEDIA_TYPE,
    headers={
      "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
      "Content-Length": str(len(document.content)),
    },
  )


@router.post("/nodes", response_model=ChapterNode, status_code=status.HTTP_201_CREATED)
async def create_chapter_node(
  project_id: str,
  request: CreateChapterNodeRequest,
  service: ChapterService = Depends(get_chapter_service),
) -> ChapterNode:
  return await service.create_node(project_id, request)


@router.patch("/nodes/{node_id}", response_model=ChapterNode)
async def update_chapter_node(
  project_id: str,
  node_id: str,
  request: UpdateChapterNodeRequest,
  service: ChapterService = Depends(get_chapter_service),
) -> ChapterNode:
  return await service.update_node(project_id, node_id, request)


@router.patch("/nodes/{node_id}/move", response_model=MoveChapterNodeResponse)
async def move_chapter_node(
  project_id: str,
  node_id: str,
  request: MoveChapterNodeRequest,
  service: ChapterService = Depends(get_chapter_service),
) -> MoveChapterNodeResponse:
  return await service.move_node(project_id, node_id, request)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter_node(
  project_id: str,
  node_id: str,
  service: ChapterService = Depends(get_chapter_service),
) -> None:
  await service.delete_node(project_id, node_id)


@router.post("", response_model=ChapterDetail, status_code=status.HTTP_201_CREATED)
async def create_chapter(
  project_id: str,
  request: CreateChapterRequest,
  service: ChapterService = Depends(get_chapter_service),
) -> ChapterDetail:
  return await service.create_chapter(project_id, request)


@router.get("/{chapter_id}", response_model=ChapterDetail)
async def get_chapter(
  project_id: str,
  chapter_id: str,
  service: ChapterService = Depends(get_chapter_service),
) -> ChapterDetail:
  return await service.get_chapter(project_id, chapter_id)


@router.put("/{chapter_id}", response_model=ChapterSaveResponse)
async def update_chapter(
  project_id: str,
  chapter_id: str,
  request: UpdateChapterRequest,
  service: ChapterService = Depends(get_chapter_service),
  project_service: ProjectService = Depends(get_project_service),
  version_service: VersionService = Depends(get_version_service),
) -> ChapterSaveResponse:
  chapter = await service.update_chapter(
    project_id,
    chapter_id,
    request.content,
    base_updated_at=request.base_updated_at,
  )
  await version_service.maybe_create_auto_version(
    project_id,
    resource_type="chapter",
    resource_id=chapter.id,
    title=chapter.title,
    content=chapter.content,
  )
  project = await project_service.get_manifest(project_id)
  return ChapterSaveResponse(**chapter.model_dump(), project=project)


@router.put(
  "/{chapter_id}/writing-synopsis",
  response_model=ChapterWritingSynopsisSaveResponse,
)
async def update_chapter_writing_synopsis(
  project_id: str,
  chapter_id: str,
  request: UpdateChapterWritingSynopsisRequest,
  service: ChapterService = Depends(get_chapter_service),
  project_service: ProjectService = Depends(get_project_service),
) -> ChapterWritingSynopsisSaveResponse:
  chapter = await service.update_chapter_writing_synopsis(
    project_id,
    chapter_id,
    request.writing_synopsis,
    base_updated_at=request.base_updated_at,
  )
  project = await project_service.get_manifest(project_id)
  return ChapterWritingSynopsisSaveResponse(**chapter.model_dump(), project=project)
