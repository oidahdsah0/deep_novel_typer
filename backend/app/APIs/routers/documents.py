from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.APIs.dependencies import (
  get_document_service,
  get_project_service,
  get_version_service,
)
from app.Services.document_service import DocumentService
from app.Services.project_service import ProjectService
from app.Services.version_service import VersionService
from app.Schemas.documents import (
  CreateDocumentNodeRequest,
  DocumentNode,
  MarkdownDocumentDetail,
  MoveDocumentNodeRequest,
  MoveDocumentNodeResponse,
  UpdateDocumentNodeRequest,
  UpdateDocumentRequest,
  WorkspaceDocument,
)
from app.Schemas.resource_saves import DocumentSaveResponse

router = APIRouter()


@router.get("", response_model=list[WorkspaceDocument])
async def list_documents(
  project_id: str,
  service: DocumentService = Depends(get_document_service),
) -> list[WorkspaceDocument]:
  return await service.list_documents(project_id)


@router.get("/tree", response_model=list[DocumentNode])
async def list_document_tree(
  project_id: str,
  service: DocumentService = Depends(get_document_service),
) -> list[DocumentNode]:
  return await service.list_document_tree(project_id)


@router.post("/nodes", response_model=DocumentNode)
async def create_document_node(
  project_id: str,
  request: CreateDocumentNodeRequest,
  service: DocumentService = Depends(get_document_service),
) -> DocumentNode:
  return await service.create_node(project_id, request)


@router.patch("/nodes/{node_id}", response_model=DocumentNode)
async def update_document_node(
  project_id: str,
  node_id: str,
  request: UpdateDocumentNodeRequest,
  service: DocumentService = Depends(get_document_service),
) -> DocumentNode:
  return await service.update_node(project_id, node_id, request)


@router.patch("/nodes/{node_id}/move", response_model=MoveDocumentNodeResponse)
async def move_document_node(
  project_id: str,
  node_id: str,
  request: MoveDocumentNodeRequest,
  service: DocumentService = Depends(get_document_service),
) -> MoveDocumentNodeResponse:
  return await service.move_node(project_id, node_id, request)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_node(
  project_id: str,
  node_id: str,
  service: DocumentService = Depends(get_document_service),
) -> None:
  await service.delete_node(project_id, node_id)


@router.get("/{document_id}", response_model=MarkdownDocumentDetail)
async def get_document(
  project_id: str,
  document_id: str,
  service: DocumentService = Depends(get_document_service),
) -> MarkdownDocumentDetail:
  return await service.get_document(project_id, document_id)


@router.put("/{document_id}", response_model=DocumentSaveResponse)
async def update_document(
  project_id: str,
  document_id: str,
  request: UpdateDocumentRequest,
  service: DocumentService = Depends(get_document_service),
  project_service: ProjectService = Depends(get_project_service),
  version_service: VersionService = Depends(get_version_service),
) -> DocumentSaveResponse:
  document = await service.update_document(
    project_id,
    document_id,
    request.content,
    base_updated_at=request.base_updated_at,
  )
  await version_service.maybe_create_auto_version(
    project_id,
    resource_type="document",
    resource_id=document.id,
    title=document.title,
    content=document.content,
  )
  project = await project_service.get_manifest(project_id)
  return DocumentSaveResponse(**document.model_dump(), project=project)
