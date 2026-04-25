from io import BytesIO
import zipfile

import pytest

from app.Services.chapter_docx_export_service import ChapterDocxExportService
from app.Utils.errors import EntityNotFoundError
from app.Schemas.chapters import CreateChapterRequest, ExportChaptersDocxRequest
from app.Schemas.projects import CreateProjectRequest
from tests.service_factories import build_services


@pytest.mark.asyncio
async def test_chapter_docx_export_includes_selected_chapters_in_reading_order(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="边境<档案>"))
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      "第一段正文\n\n第二段正文",
    )
    second = await chapter_service.create_chapter(
      project.id,
      CreateChapterRequest(title="第二章", content="异兽踩下踏板 & 发出声响"),
    )
    service = ChapterDocxExportService(project_service, chapter_service)

    exported = await service.export_chapters(
      project.id,
      ExportChaptersDocxRequest(chapter_ids=[second.id, "chapter-001"]),
    )

    assert exported.filename == "边境_档案-chapters.docx"
    with zipfile.ZipFile(BytesIO(exported.content), "r") as archive:
      assert "word/document.xml" in archive.namelist()
      document_xml = archive.read("word/document.xml").decode("utf-8")

    assert "边境&lt;档案&gt;" in document_xml
    assert "异兽踩下踏板 &amp; 发出声响" in document_xml
    assert document_xml.index("第一章") < document_xml.index("第二章")
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_chapter_docx_export_rejects_unknown_chapter(tmp_path) -> None:
  store, project_service, chapter_service, _document_service = await build_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    service = ChapterDocxExportService(project_service, chapter_service)

    with pytest.raises(EntityNotFoundError):
      await service.export_chapters(
        project.id,
        ExportChaptersDocxRequest(chapter_ids=["missing-chapter"]),
      )
  finally:
    await store.shutdown()
