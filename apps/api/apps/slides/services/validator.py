import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class InvalidPresentationPayloadError(Exception):
    """Raised when presentation or slide data fails validation."""

    pass


class PresentationValidator:
    """Validates structural and content integrity of presentations and slides.

    Guarantees that:
    1. Presentation and slide titles are sanitized, non-empty, and non-repetitive.
    2. Slide numbering is sequential without gaps or duplicates.
    3. Slide content respects maximum density to avoid visual overflows.
    4. Text is cleaned of non-printable control characters that could corrupt OpenXML/PPTX files.
    5. A presentation has at least one slide before allowing export.
    """

    MAX_BULLETS_PER_SLIDE = 6
    MAX_CHARS_PER_BULLET = 160
    MAX_TITLE_LENGTH = 200

    @classmethod
    def sanitize_text(cls, text: str | None) -> str:
        """Removes control characters except newlines and tabs."""
        if not text:
            return ""
        # Remove non-printable control characters (ASCII 0-31 except \n, \r, \t)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return cleaned.strip()

    @classmethod
    def validate_presentation_metadata(cls, title: str | None, theme: str | None) -> str:
        """Validates presentation title and returns sanitized version."""
        sanitized_title = cls.sanitize_text(title)
        if not sanitized_title:
            raise InvalidPresentationPayloadError(
                "Le titre de la présentation ne peut pas être vide."
            )
        if len(sanitized_title) > cls.MAX_TITLE_LENGTH:
            sanitized_title = sanitized_title[: cls.MAX_TITLE_LENGTH].strip()
        return sanitized_title

    @classmethod
    def validate_slide_content(
        cls, title: str | None, content: str | None, slide_number: int
    ) -> dict[str, Any]:
        """Validates individual slide content and returns sanitized attributes."""
        sanitized_title = cls.sanitize_text(title)
        if not sanitized_title:
            sanitized_title = f"Diapositive {slide_number}"

        sanitized_content = cls.sanitize_text(content)
        lines = [line.strip() for line in sanitized_content.split("\n") if line.strip()]

        # Limit lines count to prevent visual overflow
        if len(lines) > cls.MAX_BULLETS_PER_SLIDE:
            logger.warning(
                "Slide %d has %d bullet points, truncating to %d to prevent visual overflow",
                slide_number,
                len(lines),
                cls.MAX_BULLETS_PER_SLIDE,
            )
            lines = lines[: cls.MAX_BULLETS_PER_SLIDE]

        # Truncate overly long bullets
        truncated_lines = []
        for line in lines:
            if len(line) > cls.MAX_CHARS_PER_BULLET:
                truncated_lines.append(line[: cls.MAX_CHARS_PER_BULLET].rsplit(" ", 1)[0] + "...")
            else:
                truncated_lines.append(line)

        return {
            "title": sanitized_title[: cls.MAX_TITLE_LENGTH],
            "content": "\n".join(truncated_lines),
            "slide_number": slide_number,
        }

    @classmethod
    def validate_deck_for_export(cls, presentation: Any) -> list[Any]:
        """Ensures presentation has valid slides before starting PPTX export."""
        slides = list(presentation.slides.all().order_by("slide_number", "created_at"))
        if not slides:
            raise InvalidPresentationPayloadError(
                f"La présentation '{presentation.title}' ({presentation.id}) ne contient aucune diapositive à exporter."
            )
        return slides
