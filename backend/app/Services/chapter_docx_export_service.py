from __future__ import annotations

import re
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from io import BytesIO

from app.Schemas.chapters import ChapterDetail, ExportChaptersDocxRequest
from app.Services.chapter_service import ChapterService
from app.Services.project_service import ProjectService
from app.Utils.errors import EntityNotFoundError

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@dataclass(frozen=True)
class ChapterDocxExport:
  filename: str
  content: bytes


class ChapterDocxExportService:
  def __init__(
    self,
    project_service: ProjectService,
    chapter_service: ChapterService,
  ) -> None:
    self._project_service = project_service
    self._chapter_service = chapter_service

  async def export_chapters(
    self, project_id: str, request: ExportChaptersDocxRequest
  ) -> ChapterDocxExport:
    project = await self._project_service.get_manifest(project_id)
    chapter_by_id = {chapter.id: chapter for chapter in project.chapters}
    missing_ids = [
      chapter_id for chapter_id in request.chapter_ids if chapter_id not in chapter_by_id
    ]
    if missing_ids:
      raise EntityNotFoundError(f"Chapter not found: {missing_ids[0]}")

    selected_ids = set(request.chapter_ids)
    ordered_chapters = [
      await self._chapter_service.get_chapter(project_id, chapter.id)
      for chapter in project.chapters
      if chapter.id in selected_ids
    ]
    filename = _export_filename(project.title, ordered_chapters)
    return ChapterDocxExport(
      filename=filename,
      content=build_chapters_docx(project.title, ordered_chapters),
    )


def build_chapters_docx(project_title: str, chapters: Sequence[ChapterDetail]) -> bytes:
  document_xml = _document_xml(project_title, chapters)
  now = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
  files = {
    "[Content_Types].xml": _content_types_xml(),
    "_rels/.rels": _package_relationships_xml(),
    "docProps/app.xml": _app_properties_xml(len(chapters)),
    "docProps/core.xml": _core_properties_xml(project_title, now),
    "word/_rels/document.xml.rels": _document_relationships_xml(),
    "word/document.xml": document_xml,
    "word/styles.xml": _styles_xml(),
  }
  buffer = BytesIO()
  with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path, content in files.items():
      archive.writestr(path, content.encode("utf-8"))
  return buffer.getvalue()


def _document_xml(project_title: str, chapters: Sequence[ChapterDetail]) -> str:
  body_parts = [_paragraph(project_title, style="Title", alignment="center")]
  for index, chapter in enumerate(chapters):
    if index > 0:
      body_parts.append(_page_break())
    body_parts.append(_paragraph(chapter.title, style="Heading1"))
    body_parts.extend(_content_paragraphs(chapter.content))

  return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {"".join(body_parts)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1260" w:bottom="1440" w:left="1260" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""


def _content_paragraphs(content: str) -> list[str]:
  if not content:
    return [_paragraph("")]
  lines = content.splitlines()
  if not lines:
    return [_paragraph("")]
  return [_paragraph(line) if line.strip() else _paragraph("") for line in lines]


def _paragraph(text: str, *, style: str | None = None, alignment: str | None = None) -> str:
  props: list[str] = []
  if style:
    props.append(f'<w:pStyle w:val="{style}"/>')
  if alignment:
    props.append(f'<w:jc w:val="{alignment}"/>')
  if not style:
    props.append('<w:spacing w:after="180" w:line="420" w:lineRule="auto"/>')
  paragraph_props = f"<w:pPr>{''.join(props)}</w:pPr>" if props else ""
  text_node = f'<w:t xml:space="preserve">{_xml_text(text)}</w:t>'
  return f"<w:p>{paragraph_props}<w:r>{text_node}</w:r></w:p>"


def _page_break() -> str:
  return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def _xml_text(value: str) -> str:
  return escape(_strip_invalid_xml_chars(value), quote=False)


def _strip_invalid_xml_chars(value: str) -> str:
  return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", value)


def _content_types_xml() -> str:
  return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""


def _package_relationships_xml() -> str:
  return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def _document_relationships_xml() -> str:
  return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""


def _app_properties_xml(chapter_count: int) -> str:
  return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Deep Novel Typer</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Chapters</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>{chapter_count}</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="1" baseType="lpstr">
      <vt:lpstr>Chapters</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
</Properties>
"""


def _core_properties_xml(project_title: str, timestamp: str) -> str:
  return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{_xml_text(project_title)}</dc:title>
  <dc:creator>Deep Novel Typer</dc:creator>
  <cp:lastModifiedBy>Deep Novel Typer</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>
</cp:coreProperties>
"""


def _styles_xml() -> str:
  return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="SimSun" w:eastAsia="SimSun" w:hAnsi="SimSun"/>
        <w:sz w:val="24"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing w:after="360"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="36"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing w:before="360" w:after="240"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="30"/>
    </w:rPr>
  </w:style>
</w:styles>
"""


def _export_filename(project_title: str, chapters: Sequence[ChapterDetail]) -> str:
  title = _safe_filename_part(project_title) or "novel"
  if len(chapters) == 1:
    suffix = _safe_filename_part(chapters[0].title) or "chapter"
  else:
    suffix = "chapters"
  return f"{title}-{suffix}.docx"


def _safe_filename_part(value: str) -> str:
  normalized = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", value).strip(" ._")
  return re.sub(r"\s+", " ", normalized)[:80]
