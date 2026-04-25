import httpx
import pytest
from fastapi import FastAPI

from app.APIs.error_handlers import register_error_handlers


@pytest.mark.asyncio
async def test_unhandled_exception_returns_json_error() -> None:
  app = FastAPI()
  register_error_handlers(app)

  @app.get("/boom")
  async def boom():
    raise RuntimeError("database path leaked")

  transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
  async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
    response = await client.get("/boom")

  assert response.status_code == 500
  assert response.headers["content-type"].startswith("application/json")
  assert response.json() == {"detail": "Internal server error", "code": "internal_error"}
