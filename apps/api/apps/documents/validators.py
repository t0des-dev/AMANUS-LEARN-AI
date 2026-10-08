"""Validation utilities for document uploads.

Validates file extensions, size constraints, MIME types, and magic binary signatures.
"""

from pathlib import Path

from django.conf import settings
from rest_framework.exceptions import ValidationError

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}

ALLOWED_MIME_TYPES = {
    ".pdf": [
        "application/pdf",
        "application/x-pdf",
    ],
    ".docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/zip",
        "application/octet-stream",
    ],
    ".pptx": [
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-powerpoint",
        "application/zip",
        "application/octet-stream",
    ],
    ".txt": [
        "text/plain",
        "text/plain; charset=utf-8",
        "application/octet-stream",
    ],
}

# Magic byte signatures
MAGIC_SIGNATURES = {
    ".pdf": [b"%PDF-"],
    ".docx": [b"PK\x03\x04"],
    ".pptx": [b"PK\x03\x04"],
}


def validate_document_file(uploaded_file):
    """Validate uploaded document for size, extension, MIME type, and binary header.

    Raises:
        ValidationError: If any security constraint is violated.
    """
    if not uploaded_file:
        raise ValidationError({"file": "Aucun fichier n'a été fourni."})

    # 1. Size Validation
    max_size = getattr(settings, "MAX_DOCUMENT_SIZE", 50 * 1024 * 1024)
    file_size = getattr(uploaded_file, "size", 0)
    if file_size <= 0:
        raise ValidationError({"file": "Le fichier est vide (0 octet)."})
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(
            {"file": f"La taille du fichier dépasse la limite autorisée ({max_mb:.0f} Mo)."}
        )

    # 2. Extension Validation
    file_name = getattr(uploaded_file, "name", "")
    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            {
                "file": (
                    f"Format '{extension}' non supporté. Formats acceptés : "
                    f"{', '.join(sorted(ALLOWED_EXTENSIONS))}."
                )
            }
        )

    # 3. MIME Type Validation
    content_type = getattr(uploaded_file, "content_type", "").lower()
    allowed_mimes = ALLOWED_MIME_TYPES.get(extension, [])
    # If content_type is provided, ensure it matches permitted variants
    if content_type and not any(mime in content_type for mime in allowed_mimes):
        raise ValidationError(
            {"file": (f"Type MIME non autorisé ({content_type}) pour l'extension {extension}.")}
        )

    # 4. Header Signature Check (Magic Bytes)
    signatures = MAGIC_SIGNATURES.get(extension)
    if signatures:
        initial_pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
        header = uploaded_file.read(8)
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(initial_pos)

        matches = any(header.startswith(sig) for sig in signatures)
        if not matches:
            raise ValidationError(
                {
                    "file": (
                        f"Le contenu binaire du fichier ne correspond pas à l'extension {extension}."
                    )
                }
            )

    return True
