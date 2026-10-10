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

# Configurable processing thresholds to protect memory and workers
MAX_EXTRACT_PAGES = 500
MAX_EXTRACT_CHARS = 1_000_000
MIN_PAGE_CHAR_THRESHOLD = 20


class PDFParser(DocumentParser):
    """Adapter for parsing Adobe Portable Document Format (.pdf) files.

    Maintains page boundaries, reading order, scans/OCR detection,
    and enforces page and character budgets to prevent worker denial of service.
    """

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
        global_metadata: dict = {"warnings": []}
        warnings: list[str] = global_metadata["warnings"]

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

        pages_to_process = total_pages
        if total_pages > MAX_EXTRACT_PAGES:
            warnings.append(f"MAX_PAGES_LIMIT_REACHED_{MAX_EXTRACT_PAGES}_OF_{total_pages}")
            pages_to_process = MAX_EXTRACT_PAGES

        accumulated_chars = 0

        for idx in range(pages_to_process):
            page = reader.pages[idx]
            page_num = idx + 1
            raw_text = ""
            try:
                raw_text = page.extract_text() or ""
            except Exception as e:
                logger.warning(f"[PDFParser] Failed extracting text from page {page_num}: {e}")
                warnings.append(f"PAGE_{page_num}_EXTRACTION_ERROR")

            clean_text = normalize_text(raw_text)
            ocr_used = False
            page_warnings: list[str] = []

            # Check if page is scanned/image-only
            has_images = hasattr(page, "images") and len(page.images) > 0
            if len(clean_text) < MIN_PAGE_CHAR_THRESHOLD:
                if has_images:
                    ocr_available = self.ocr_parser.is_available()
                    if ocr_available:
                        try:
                            for img in page.images:
                                ocr_result = self.ocr_parser.parse_image_bytes(img.data)
                                if ocr_result:
                                    clean_text = (clean_text + "\n" + ocr_result).strip()
                                    ocr_used = True
                        except Exception as e:
                            logger.debug(f"[PDFParser] OCR attempt on page {page_num} failed: {e}")
                            page_warnings.append(f"PAGE_{page_num}_OCR_FAILED")
                    else:
                        page_warnings.append(f"PAGE_{page_num}_SCANNED_NEEDS_OCR")
                        if "DOCUMENT_CONTAINS_SCANNED_PAGES_WITHOUT_OCR" not in warnings:
                            warnings.append("DOCUMENT_CONTAINS_SCANNED_PAGES_WITHOUT_OCR")
                else:
                    page_warnings.append(f"PAGE_{page_num}_EMPTY")

            accumulated_chars += len(clean_text)
            struct_info = detect_structure(clean_text)
            page_meta = {
                "page_number": page_num,
                "chapter": struct_info.get("chapter"),
                "section": struct_info.get("section"),
                "subsection": struct_info.get("subsection"),
                "char_count": len(clean_text),
                "headings": struct_info.get("headings", []),
                "ocr_needed": has_images and len(clean_text) < MIN_PAGE_CHAR_THRESHOLD and not ocr_used,
                "is_empty": len(clean_text) < MIN_PAGE_CHAR_THRESHOLD,
                "warnings": page_warnings,
            }

            pages.append(
                ParsedPage(
                    page_number=page_num,
                    text=clean_text,
                    ocr_used=ocr_used,
                    metadata=page_meta,
                )
            )

            # Check total volume limit
            if accumulated_chars >= MAX_EXTRACT_CHARS:
                warnings.append("MAX_CHARS_LIMIT_REACHED")
                break

        return ParsedDocument(pages=pages, metadata=global_metadata)
