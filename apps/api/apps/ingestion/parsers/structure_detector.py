import re
from typing import Any

CHAPTER_PATTERNS = [
    re.compile(
        r"^(?:#\s+|chapitre\s+[\d\.]+|chapter\s+[\d\.]+|module\s+[\d\.]+|partie\s+[ivxlcdm\d\.]+|part\s+[ivxlcdm\d\.]+)(?:\s*[:\-–]\s*|\s+)(.+)$",
        re.IGNORECASE,
    ),
    re.compile(r"^(?:chapitre|chapter|module|partie|part)\s+[\d\.]+.*$", re.IGNORECASE),
    re.compile(r"^#\s+(.+)$"),
]

SECTION_PATTERNS = [
    re.compile(
        r"^(?:##\s+|section\s+[\d\.]+|partie\s+[\d\.]+)(?:\s*[:\-–]\s*|\s+)(.+)$", re.IGNORECASE
    ),
    re.compile(r"^section\s+[\d\.]+.*$", re.IGNORECASE),
    re.compile(r"^(\d+\.\d+)(?:\s*[:\-–]\s*|\s+)([A-ZÀ-ÿ].*)$"),
    re.compile(r"^##\s+(.+)$"),
]

SUBSECTION_PATTERNS = [
    re.compile(
        r"^(?:###\s+|sous-section\s+[\d\.]+|subsection\s+[\d\.]+)(?:\s*[:\-–]\s*|\s+)(.+)$",
        re.IGNORECASE,
    ),
    re.compile(r"^(?:sous-section|subsection)\s+[\d\.]+.*$", re.IGNORECASE),
    re.compile(r"^(\d+\.\d+\.\d+)(?:\s*[:\-–]\s*|\s+)([A-ZÀ-ÿ].*)$"),
    re.compile(r"^###\s+(.+)$"),
]


def detect_structure(text: str) -> dict[str, Any]:
    """Scans text lines to detect hierarchical headings (chapter, section, subsection).

    Returns a dictionary with the detected hierarchical elements.
    """
    if not text:
        return {
            "chapter": None,
            "section": None,
            "subsection": None,
            "headings": [],
        }

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    current_chapter: str | None = None
    current_section: str | None = None
    current_subsection: str | None = None
    headings: list[str] = []

    for line in lines:
        matched = False

        # Chapter check
        for pattern in CHAPTER_PATTERNS:
            match = pattern.match(line)
            if match:
                current_chapter = line
                headings.append(line)
                matched = True
                break

        if matched:
            continue

        # Section check
        for pattern in SECTION_PATTERNS:
            match = pattern.match(line)
            if match:
                current_section = line
                headings.append(line)
                matched = True
                break

        if matched:
            continue

        # Subsection check
        for pattern in SUBSECTION_PATTERNS:
            match = pattern.match(line)
            if match:
                current_subsection = line
                headings.append(line)
                matched = True
                break

    return {
        "chapter": current_chapter,
        "section": current_section,
        "subsection": current_subsection,
        "headings": headings,
    }
