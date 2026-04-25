from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.Utils.errors import (
  DomainError,
  EntityConflictError,
  EntityNotFoundError,
  InvalidProjectPathError,
  LLMContextWindowExceededError,
  LLMNotConfiguredError,
  LLMRequestError,
  LLMResponseFormatError,
)

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
  @app.exception_handler(EntityNotFoundError)
  async def not_found_handler(_request: Request, exc: EntityNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

  @app.exception_handler(EntityConflictError)
  async def conflict_handler(_request: Request, exc: EntityConflictError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

  @app.exception_handler(InvalidProjectPathError)
  async def invalid_path_handler(_request: Request, exc: InvalidProjectPathError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

  @app.exception_handler(LLMResponseFormatError)
  async def llm_response_format_handler(
    _request: Request, exc: LLMResponseFormatError
  ) -> JSONResponse:
    return JSONResponse(
      status_code=status.HTTP_502_BAD_GATEWAY,
      content={"detail": str(exc), "code": "llm_response_schema_error"},
    )

  @app.exception_handler(LLMContextWindowExceededError)
  async def llm_context_window_handler(
    _request: Request, exc: LLMContextWindowExceededError
  ) -> JSONResponse:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"detail": str(exc), "code": "llm_context_window_exceeded"},
    )

  @app.exception_handler(LLMNotConfiguredError)
  async def llm_not_configured_handler(
    _request: Request, exc: LLMNotConfiguredError
  ) -> JSONResponse:
    return JSONResponse(
      status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
      content={"detail": str(exc), "code": "llm_not_configured"},
    )

  @app.exception_handler(LLMRequestError)
  async def llm_request_handler(_request: Request, exc: LLMRequestError) -> JSONResponse:
    return JSONResponse(
      status_code=status.HTTP_502_BAD_GATEWAY,
      content={"detail": str(exc), "code": "llm_request_failed"},
    )

  @app.exception_handler(DomainError)
  async def domain_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

  @app.exception_handler(Exception)
  async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error for %s %s", request.method, request.url.path)
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"detail": "Internal server error", "code": "internal_error"},
    )
