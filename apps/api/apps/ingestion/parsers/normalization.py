import re
import unicodedata


def normalize_text(text: str | None) -> str:
    """Normalizes raw extracted text for downstream processing.

    - Converts to Unicode NFKC.
    - Standardizes line breaks to '\n'.
    - Removes null bytes and control characters (preserving tab and newline).
    - Cleans non-breaking spaces and excessive consecutive whitespaces/newlines.
    """
    if not text:
        return ""

    # Remove null bytes immediately
    text = text.replace("\x00", "")

    # Normalize unicode to NFKC
    text = unicodedata.normalize("NFKC", text)

    # Standardize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace non-breaking spaces and tabs with standard space (or keep tabs)
    text = text.replace("\u00a0", " ").replace("\u202f", " ")

    # Strip unprintable control characters, keeping newline, tab, and standard characters
    # (ASCII < 32 except \t (9) and \n (10))
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # Collapse multiple horizontal whitespaces (except newlines)
    lines = text.split("\n")
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    text = "\n".join(cleaned_lines)

    # Collapse more than two consecutive empty lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
