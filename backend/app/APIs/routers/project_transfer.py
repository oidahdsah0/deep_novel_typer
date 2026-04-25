from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request, Response

from app.APIs.dependencies import get_project_transfer_service
from app.Services.project_transfer import ProjectTransferService
from app.Schemas.project_transfer import ProjectExportOptions, ProjectImportResponse

router = APIRouter()


@router.get("/{project_id}/export")
async def export_project(
  project_id: str,
  include_debug_logs: bool = Query(default=False),
  include_token_usage: bool = Query(default=False),
  include_api_config_summary: bool = Query(default=True),
  service: ProjectTransferService = Depends(get_project_transfer_service),
) -> Response:
  archive = await service.export_project(
    project_id,
    ProjectExportOptions(
      include_debug_logs=include_debug_logs,
      include_token_usage=include_token_usage,
      include_api_config_summary=include_api_config_summary,
    ),
  )
  filename = quote(f"{project_id}-deep-novel-export.zip")
  return Response(
    content=archive,
    media_type="application/zip",
    headers={
      "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
      "Content-Length": str(len(archive)),
    },
  )


@router.post("/import", response_model=ProjectImportResponse)
async def import_project(
  request: Request,
  service: ProjectTransferService = Depends(get_project_transfer_service),
) -> ProjectImportResponse:
  return await service.import_project(await request.body())
