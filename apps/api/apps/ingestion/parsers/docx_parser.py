import io
import logging
from typing import BinaryIO

import docx
from docx.opc.exceptions import PackageNotFoundError

from .base import DocumentParser, InvalidDocumentFileError, ParsedDocument, ParsedPage
from .normalization import normalize_text
from .structure_detector import detect_structure

logger = logging.getLogger(__name__)


class DOCXParser(DocumentParser):
    """Adapter for parsing Microsoft Word (.docx) files."""

    def parse(self, file_source: bytes | BinaryIO, **kwargs) -> ParsedDocument:
        if isinstance(file_source, bytes):
            stream = io.BytesIO(file_source)
        else:
            stream = file_source

        try:
            doc = docx.Document(stream)
        except (PackageNotFoundError, Exception) as e:
            raise InvalidDocumentFileError(f"Fichier DOCX invalide ou corrompu : {e}") from e

        global_metadata: dict = {}
        try:
            core_props = doc.core_properties
            if core_props:
                if core_props.title:
                    global_metadata["title"] = core_props.title
                if core_props.author:
                    global_metadata["author"] = core_props.author
                if core_props.subject:
                    global_metadata["subject"] = core_props.subject
        except Exception as e:
            logger.debug(f"[DOCXParser] Error extracting core properties: {e}")

        # Extract text blocks while tracking headings and logical page breaks
        pages_content: list[list[str]] = [[]]
        current_page_idx = 0
        current_page_chars = 0
        PAGE_CHAR_THRESHOLD = 2500  # Estimate ~1 standard A4 page per 2500 characters

        # Traverse paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Check for explicit page break in paragraph runs
            has_explicit_break = False
            for run in para.runs:
                if "w:br" in run._r.xml and 'w:type="page"' in run._r.xml:
                    has_explicit_break = True
                    break

            if has_explicit_break and len(pages_content[current_page_idx]) > 0:
                pages_content.append([])
                current_page_idx += 1
                current_page_chars = 0

            # Style tag detection
            style_name = para.style.name.lower() if para.style and para.style.name else ""
            if "heading 1" in style_name:
                formatted_para = f"# {text}"
            elif "heading 2" in style_name:
                formatted_para = f"## {text}"
            elif "heading 3" in style_name:
                formatted_para = f"### {text}"
            else:
                formatted_para = text

            pages_content[current_page_idx].append(formatted_para)
            current_page_chars += len(formatted_para)

            # If page length threshold reached and at a paragraph boundary, create new logical page
            if current_page_chars >= PAGE_CHAR_THRESHOLD:
                pages_content.append([])
                current_page_idx += 1
                current_page_chars = 0

        # Traverse tables
        for table in doc.tables:
            table_lines: list[str] = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_lines.append(" | ".join(row_cells))
            if table_lines:
                table_text = "\n".join(table_lines)
                pages_content[current_page_idx].append(f"[Tableau]\n{table_text}")
                current_page_chars += len(table_text)
                if current_page_chars >= PAGE_CHAR_THRESHOLD:
                    pages_content.append([])
                    current_page_idx += 1
                    current_page_chars = 0

        # Filter out empty pages
        cleaned_pages_data = [
            "\n\n".join(blocks)
            for blocks in pages_content
            if any(block.strip() for block in blocks)
        ]

        if not cleaned_pages_data:
            cleaned_pages_data = [""]

        pages: list[ParsedPage] = []
        running_chapter: str | None = None
        running_section: str | None = None
        running_subsection: str | None = None

        for idx, page_raw in enumerate(cleaned_pages_data):
            page_num = idx + 1
            clean_text = normalize_text(page_raw)
            struct_info = detect_structure(clean_text)

            if struct_info.get("chapter"):
                running_chapter = struct_info["chapter"]
            if struct_info.get("section"):
                running_section = struct_info["section"]
            if struct_info.get("subsection"):
                running_subsection = struct_info["subsection"]

            page_meta = {
                "page_number": page_num,
                "chapter": struct_info.get("chapter") or running_chapter,
                "section": struct_info.get("section") or running_section,
                "subsection": struct_info.get("subsection") or running_subsection,
                "char_count": len(clean_text),
                "headings": struct_info.get("headings", []),
            }

            pages.append(
                ParsedPage(
                    page_number=page_num,
                    text=clean_text,
                    ocr_used=False,
                    metadata=page_meta,
                )
            )

        return ParsedDocument(pages=pages, metadata=global_metadata)
