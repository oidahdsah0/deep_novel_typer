from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


@dataclass(frozen=True)
class CachedEmbedding:
  id: str
  embedding: list[float]
  document: str
  metadata: dict[str, object]


class ChromaEmbeddingStore:
  def __init__(self, path: Path) -> None:
    self._path = path
    self._client = None
    self._client_lock = asyncio.Lock()

  async def get_embeddings(
    self, collection_name: str, ids: list[str]
  ) -> dict[str, CachedEmbedding]:
    if not ids:
      return {}
    client = await self._client_instance()
    return await asyncio.to_thread(self._get_embeddings_sync, client, collection_name, ids)

  async def upsert_embeddings(
    self,
    collection_name: str,
    *,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict[str, object]],
  ) -> None:
    if not ids:
      return
    client = await self._client_instance()
    await asyncio.to_thread(
      self._upsert_embeddings_sync,
      client,
      collection_name,
      ids,
      embeddings,
      documents,
      metadatas,
    )

  def _get_embeddings_sync(
    self, client, collection_name: str, ids: list[str]
  ) -> dict[str, CachedEmbedding]:
    collection = self._collection(client, collection_name)
    result = collection.get(ids=ids, include=["embeddings", "documents", "metadatas"])
    embeddings = result.get("embeddings")
    documents = result.get("documents")
    metadatas = result.get("metadatas")
    embeddings = [] if embeddings is None else embeddings
    documents = [] if documents is None else documents
    metadatas = [] if metadatas is None else metadatas
    found: dict[str, CachedEmbedding] = {}
    for index, item_id in enumerate(result.get("ids") or []):
      vector = embeddings[index]
      if hasattr(vector, "tolist"):
        vector = vector.tolist()
      found[item_id] = CachedEmbedding(
        id=item_id,
        embedding=[float(value) for value in vector],
        document=str(documents[index] if index < len(documents) else ""),
        metadata=dict(metadatas[index] if index < len(metadatas) and metadatas[index] else {}),
      )
    return found

  def _upsert_embeddings_sync(
    self,
    client,
    collection_name: str,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict[str, object]],
  ) -> None:
    collection = self._collection(client, collection_name)
    collection.upsert(
      ids=ids,
      embeddings=embeddings,
      documents=documents,
      metadatas=[_clean_metadata(metadata) for metadata in metadatas],
    )

  def _collection(self, client, collection_name: str):
    return client.get_or_create_collection(collection_name)

  async def _client_instance(self):
    if self._client is None:
      async with self._client_lock:
        if self._client is None:
          self._client = await asyncio.to_thread(self._create_client)
    return self._client

  def _create_client(self):
    self._path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
      path=str(self._path),
      settings=Settings(anonymized_telemetry=False),
    )


def _clean_metadata(metadata: dict[str, object]) -> dict[str, str | int | float | bool]:
  cleaned: dict[str, str | int | float | bool] = {}
  for key, value in metadata.items():
    if value is None:
      continue
    if isinstance(value, (str, int, float, bool)):
      cleaned[key] = value
    else:
      cleaned[key] = str(value)
  return cleaned
