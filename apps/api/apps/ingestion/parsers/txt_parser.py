from typing import BinaryIO

from .base import DocumentParser, InvalidDocumentFileError, ParsedDocument, ParsedPage
from .normalization import normalize_text
from .structure_detector import detect_structure


class TXTParser(DocumentParser):
    """Adapter for parsing plain text (.txt) files."""

    def parse(self, file_source: bytes | BinaryIO, **kwargs) -> ParsedDocument:
        if isinstance(file_source, bytes):
            raw_bytes = file_source
        else:
            raw_bytes = file_source.read()

        # Attempt multiple encodings
        text: str = ""
        decoded = False
        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-15"]:
            try:
                text = raw_bytes.decode(encoding)
                decoded = True
                break
            except UnicodeDecodeError:
                continue

        if not decoded:
            raise InvalidDocumentFileError(
                "Impossible de décoder le fichier texte (encodage inconnu)."
            )

        normalized_full = normalize_text(text)
        if not normalized_full:
            raise InvalidDocumentFileError("Le fichier texte est vide.")

        # Check for explicit form-feed page separators (\f)
        if "\x0c" in text:
            raw_pages = text.split("\x0c")
        else:
            # Segment logically into ~2500 character pages at paragraph boundaries
            paragraphs = normalized_full.split("\n\n")
            raw_pages = []
            current_page_blocks: list[str] = []
            current_len = 0
            PAGE_THRESHOLD = 2500

            for p in paragraphs:
                p_len = len(p)
                if current_len + p_len > PAGE_THRESHOLD and current_page_blocks:
                    raw_pages.append("\n\n".join(current_page_blocks))
                    current_page_blocks = [p]
                    current_len = p_len
                else:
                    current_page_blocks.append(p)
                    current_len += p_len

            if current_page_blocks:
                raw_pages.append("\n\n".join(current_page_blocks))

        pages: list[ParsedPage] = []
        running_chapter: str | None = None
        running_section: str | None = None
        running_subsection: str | None = None

        for idx, page_content in enumerate(raw_pages):
            page_num = idx + 1
            clean_page_text = normalize_text(page_content)
            struct_info = detect_structure(clean_page_text)

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
                "char_count": len(clean_page_text),
                "headings": struct_info.get("headings", []),
            }

            pages.append(
                ParsedPage(
                    page_number=page_num,
                    text=clean_page_text,
                    ocr_used=False,
                    metadata=page_meta,
                )
            )

        return ParsedDocument(pages=pages, metadata={"format": "txt"})
