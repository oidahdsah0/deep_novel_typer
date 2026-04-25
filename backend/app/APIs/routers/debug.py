from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status

from app.APIs.dependencies import get_debug_log_service, get_model_request_queue_service
from app.Services.model_request_queue_service import ModelRequestQueueService
from app.Services.debug_log_service import DebugLogService
from app.Schemas.debug import DebugRequestLog, DebugSnapshot, DebugTokenUsage
from app.Schemas.model_queue import ModelQueueSnapshot

router = APIRouter()


@router.get("", response_model=DebugSnapshot)
async def get_debug_snapshot(
  project_id: str | None = Query(default=None),
  service: DebugLogService = Depends(get_debug_log_service),
) -> DebugSnapshot:
  return await service.snapshot(project_id)


@router.get("/token-usage", response_model=DebugTokenUsage)
async def get_token_usage(
  project_id: str | None = Query(default=None),
  service: DebugLogService = Depends(get_debug_log_service),
) -> DebugTokenUsage:
  return await service.token_usage(project_id)


@router.get("/request-logs", response_model=list[DebugRequestLog])
async def get_request_logs(
  project_id: str | None = Query(default=None),
  limit: int = Query(default=50, ge=1, le=50),
  service: DebugLogService = Depends(get_debug_log_service),
) -> list[DebugRequestLog]:
  return await service.request_logs(project_id=project_id, limit=limit)


@router.get("/model-queue", response_model=ModelQueueSnapshot)
async def get_model_queue_snapshot(
  service: ModelRequestQueueService = Depends(get_model_request_queue_service),
) -> ModelQueueSnapshot:
  return await service.snapshot()


@router.delete("/token-usage", status_code=status.HTTP_204_NO_CONTENT)
async def clear_token_usage(
  project_id: str | None = Query(default=None),
  service: DebugLogService = Depends(get_debug_log_service),
) -> Response:
  await service.clear_token_usage(project_id)
  return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/request-logs", status_code=status.HTTP_204_NO_CONTENT)
async def clear_request_logs(
  project_id: str | None = Query(default=None),
  service: DebugLogService = Depends(get_debug_log_service),
) -> Response:
  await service.clear_request_logs(project_id)
  return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def clear_debug_data(
  project_id: str | None = Query(default=None),
  service: DebugLogService = Depends(get_debug_log_service),
) -> Response:
  await service.clear_all(project_id)
  return Response(status_code=status.HTTP_204_NO_CONTENT)
