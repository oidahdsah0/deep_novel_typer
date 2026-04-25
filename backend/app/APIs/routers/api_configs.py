from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.APIs.dependencies import get_api_config_service
from app.Services.api_configs import APIConfigService
from app.Schemas.api_configs import (
  APIConfig,
  APIConfigHealthCheckResult,
  APIConfigTemplate,
  CreateAPIConfigRequest,
  UpdateAPIConfigRequest,
)

router = APIRouter()


@router.get("", response_model=list[APIConfig])
async def list_api_configs(
  service: APIConfigService = Depends(get_api_config_service),
) -> list[APIConfig]:
  return await service.list_configs()


@router.get("/templates", response_model=list[APIConfigTemplate])
async def list_api_config_templates(
  service: APIConfigService = Depends(get_api_config_service),
) -> list[APIConfigTemplate]:
  return service.list_templates()


@router.post("", response_model=APIConfig, status_code=status.HTTP_201_CREATED)
async def create_api_config(
  request: CreateAPIConfigRequest,
  service: APIConfigService = Depends(get_api_config_service),
) -> APIConfig:
  return await service.create_config(request)


@router.put("/{config_id}", response_model=APIConfig)
async def update_api_config(
  config_id: str,
  request: UpdateAPIConfigRequest,
  service: APIConfigService = Depends(get_api_config_service),
) -> APIConfig:
  return await service.update_config(config_id, request)


@router.post("/{config_id}/health-check", response_model=APIConfigHealthCheckResult)
async def health_check_api_config(
  config_id: str,
  service: APIConfigService = Depends(get_api_config_service),
) -> APIConfigHealthCheckResult:
  return await service.health_check(config_id)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_config(
  config_id: str,
  service: APIConfigService = Depends(get_api_config_service),
) -> None:
  await service.delete_config(config_id)


@router.put("/{config_id}/default", response_model=APIConfig)
async def set_default_api_config(
  config_id: str,
  service: APIConfigService = Depends(get_api_config_service),
) -> APIConfig:
  return await service.set_default(config_id)
