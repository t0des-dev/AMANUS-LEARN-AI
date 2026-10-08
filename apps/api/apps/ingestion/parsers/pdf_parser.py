import io
import logging
from typing import BinaryIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .base import DocumentParser, InvalidDocumentFileError, ParsedDocument, ParsedPage
from .normalization import normalize_text
from .ocr_parser import OCRParser
from .structure_detector import detect_structure

logger = logging.getLogger(__name__)


class PDFParser(DocumentParser):
    """Adapter for parsing Adobe Portable Document Format (.pdf) files."""

    def __init__(self, ocr_parser: OCRParser | None = None):
        self.ocr_parser = ocr_parser or OCRParser()

    def parse(self, file_source: bytes | BinaryIO, **kwargs) -> ParsedDocument:
        if isinstance(file_source, bytes):
            stream = io.BytesIO(file_source)
        else:
            stream = file_source

        try:
            reader = PdfReader(stream)
        except (PdfReadError, Exception) as e:
            raise InvalidDocumentFileError(f"Fichier PDF invalide ou corrompu : {e}") from e

        if reader.is_encrypted:
            try:
                # Try empty password default
                reader.decrypt("")
            except Exception as e:
                raise InvalidDocumentFileError(
                    f"Le fichier PDF est protégé par mot de passe : {e}"
                ) from e

        pages: list[ParsedPage] = []
        global_metadata: dict = {}

        if reader.metadata:
            try:
                for k, v in reader.metadata.items():
                    if v and isinstance(v, (str, int, float)):
                        clean_key = str(k).lstrip("/").lower()
                        global_metadata[clean_key] = str(v)
            except Exception as e:
                logger.debug(f"[PDFParser] Error reading global PDF metadata: {e}")

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise InvalidDocumentFileError("Le document PDF ne contient aucune page.")

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            raw_text = ""
            try:
                raw_text = page.extract_text() or ""
            except Exception as e:
                logger.warning(f"[PDFParser] Failed extracting text from page {page_num}: {e}")

            clean_text = normalize_text(raw_text)
            ocr_used = False

            # Check if page is scanned/empty and has images for OCR
            if len(clean_text) < 40 and hasattr(page, "images") and len(page.images) > 0:
                try:
                    for img in page.images:
                        ocr_result = self.ocr_parser.parse_image_bytes(img.data)
                        if ocr_result:
                            clean_text = (clean_text + "\n" + ocr_result).strip()
                            ocr_used = True
                except Exception as e:
                    logger.debug(f"[PDFParser] OCR attempt on page {page_num} images skipped: {e}")

            struct_info = detect_structure(clean_text)
            page_meta = {
                "page_number": page_num,
                "chapter": struct_info.get("chapter"),
                "section": struct_info.get("section"),
                "subsection": struct_info.get("subsection"),
                "char_count": len(clean_text),
                "headings": struct_info.get("headings", []),
            }

            pages.append(
                ParsedPage(
                    page_number=page_num,
                    text=clean_text,
                    ocr_used=ocr_used,
                    metadata=page_meta,
                )
            )

        return ParsedDocument(pages=pages, metadata=global_metadata)
