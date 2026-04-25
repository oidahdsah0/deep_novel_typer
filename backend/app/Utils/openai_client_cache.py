from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI


@dataclass(frozen=True)
class OpenAIClientCacheKey:
  base_url: str
  api_key_hash: str
  headers_hash: str
  timeout_seconds: float


_CLIENTS: dict[OpenAIClientCacheKey, AsyncOpenAI] = {}
_LOCK = asyncio.Lock()


async def get_cached_openai_client(
  *,
  api_key: str,
  base_url: str,
  headers: dict[str, str] | None,
  timeout_seconds: float,
) -> AsyncOpenAI:
  key = _cache_key(
    api_key=api_key,
    base_url=base_url,
    headers=headers,
    timeout_seconds=timeout_seconds,
  )
  client = _CLIENTS.get(key)
  if client is not None:
    return client

  async with _LOCK:
    client = _CLIENTS.get(key)
    if client is None:
      client = AsyncOpenAI(
        api_key=api_key or "unused",
        base_url=base_url,
        default_headers=headers or {},
        timeout=timeout_seconds,
      )
      _CLIENTS[key] = client
    return client


async def close_cached_openai_clients() -> None:
  async with _LOCK:
    clients = list(_CLIENTS.values())
    _CLIENTS.clear()
  for client in clients:
    await client.close()


def _cache_key(
  *,
  api_key: str,
  base_url: str,
  headers: dict[str, str] | None,
  timeout_seconds: float,
) -> OpenAIClientCacheKey:
  return OpenAIClientCacheKey(
    base_url=base_url,
    api_key_hash=_hash_secret(api_key),
    headers_hash=_hash_json(headers or {}),
    timeout_seconds=timeout_seconds,
  )


def _hash_secret(value: str) -> str:
  return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_json(value: dict[str, Any]) -> str:
  payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
  return hashlib.sha256(payload.encode("utf-8")).hexdigest()
