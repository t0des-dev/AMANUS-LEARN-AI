from .base import (
    DocumentParser,
    InvalidDocumentFileError,
    ParsedDocument,
    ParsedPage,
    UnsupportedDocumentFormatError,
)
from .docx_parser import DOCXParser
from .normalization import normalize_text
from .ocr_parser import OCRParser
from .pdf_parser import PDFParser
from .pptx_parser import PPTXParser
from .structure_detector import detect_structure
from .txt_parser import TXTParser


class DocumentParserFactory:
    """Factory responsible for file format detection and adapter dispatch."""

    @classmethod
    def get_parser(cls, file_type: str, **kwargs) -> DocumentParser:
        normalized = file_type.lower().strip().lstrip(".")
        if "/" in normalized:
            # Handle mime types if passed
            mime_map = {
                "application/pdf": "pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
                "text/plain": "txt",
            }
            normalized = mime_map.get(normalized, normalized)

        if normalized == "pdf":
            return PDFParser(**kwargs)
        elif normalized in ("docx", "doc"):
            return DOCXParser()
        elif normalized in ("pptx", "ppt"):
            return PPTXParser()
        elif normalized in ("txt", "text", "md", "markdown"):
            return TXTParser()
        else:
            raise UnsupportedDocumentFormatError(
                f"Format de document non supporté pour l'ingestion : '{file_type}'. "
                "Formats acceptés : PDF, DOCX, PPTX, TXT."
            )


__all__ = [
    "DocumentParser",
    "PDFParser",
    "DOCXParser",
    "PPTXParser",
    "TXTParser",
    "OCRParser",
    "DocumentParserFactory",
    "ParsedDocument",
    "ParsedPage",
    "UnsupportedDocumentFormatError",
    "InvalidDocumentFileError",
    "normalize_text",
    "detect_structure",
]
