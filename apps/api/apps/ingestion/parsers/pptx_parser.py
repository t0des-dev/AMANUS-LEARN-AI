import io
import logging
from typing import BinaryIO

import pptx

from .base import DocumentParser, InvalidDocumentFileError, ParsedDocument, ParsedPage
from .normalization import normalize_text
from .structure_detector import detect_structure

logger = logging.getLogger(__name__)


class PPTXParser(DocumentParser):
    """Adapter for parsing Microsoft PowerPoint (.pptx) presentations."""

    def parse(self, file_source: bytes | BinaryIO, **kwargs) -> ParsedDocument:
        if isinstance(file_source, bytes):
            stream = io.BytesIO(file_source)
        else:
            stream = file_source

        try:
            prs = pptx.Presentation(stream)
        except Exception as e:
            raise InvalidDocumentFileError(f"Fichier PPTX invalide ou corrompu : {e}") from e

        global_metadata: dict = {}
        try:
            core_props = prs.core_properties
            if core_props:
                if core_props.title:
                    global_metadata["title"] = core_props.title
                if core_props.author:
                    global_metadata["author"] = core_props.author
        except Exception as e:
            logger.debug(f"[PPTXParser] Error extracting core properties: {e}")

        pages: list[ParsedPage] = []
        total_slides = len(prs.slides)
        if total_slides == 0:
            raise InvalidDocumentFileError("La présentation PPTX ne contient aucune diapositive.")

        for idx, slide in enumerate(prs.slides):
            page_num = idx + 1
            slide_elements: list[str] = []
            slide_title: str | None = None

            # Check title placeholder if available
            try:
                if slide.shapes.title and slide.shapes.title.text.strip():
                    slide_title = slide.shapes.title.text.strip()
                    slide_elements.append(f"# {slide_title}")
            except Exception:
                pass

            # Extract text from shapes and tables
            for shape in slide.shapes:
                # Avoid duplicating slide title
                if slide_title and hasattr(shape, "text") and shape.text.strip() == slide_title:
                    continue

                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text = paragraph.text.strip()
                        if text:
                            slide_elements.append(text)

                elif shape.has_table:
                    table_rows: list[str] = []
                    for row in shape.table.rows:
                        cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if cells:
                            table_rows.append(" | ".join(cells))
                    if table_rows:
                        slide_elements.append("[Tableau]\n" + "\n".join(table_rows))

            # Extract speaker notes if any
            try:
                if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                    notes = slide.notes_slide.notes_text_frame.text.strip()
                    if notes:
                        slide_elements.append(f"[Notes de présentation]\n{notes}")
            except Exception:
                pass

            raw_slide_text = "\n\n".join(slide_elements)
            clean_text = normalize_text(raw_slide_text)

            struct_info = detect_structure(clean_text)
            page_meta = {
                "page_number": page_num,
                "slide_title": slide_title,
                "chapter": struct_info.get("chapter")
                or (f"Diapositive {page_num}" if not slide_title else None),
                "section": struct_info.get("section") or slide_title,
                "subsection": struct_info.get("subsection"),
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
