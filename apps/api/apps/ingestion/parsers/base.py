from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, BinaryIO


@dataclass
class ParsedPage:
    """Represents a single parsed page or logical slice of a document."""

    page_number: int
    text: str
    ocr_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Represents the complete parsed document containing its pages and global metadata."""

    pages: list[ParsedPage] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text)


class DocumentParser(ABC):
    """Abstract base adapter for all document format parsers."""

    @abstractmethod
    def parse(self, file_source: bytes | BinaryIO, **kwargs) -> ParsedDocument:
        """Parses a document from raw bytes or a binary stream into a ParsedDocument."""
        pass


class UnsupportedDocumentFormatError(ValueError):
    """Raised when an unsupported document format is passed to the parser factory."""

    pass


class InvalidDocumentFileError(ValueError):
    """Raised when a document file is corrupted, malformed, or cannot be parsed."""

    pass
