"""Validation utilities for document uploads.

Validates file extensions, size constraints, MIME types, binary headers,
file path traversal, decompression bombs, and active macro components.
"""

import io
import zipfile
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

# Security limits for decompression and archive inspection
MAX_UNCOMPRESSED_ARCHIVE_BYTES = 150 * 1024 * 1024  # 150 MB
MAX_DECOMPRESSION_RATIO = 50.0  # Zip bomb ratio threshold


def sanitize_file_name(file_name: str) -> str:
    """Sanitize filename to prevent directory traversal and special control characters."""
    if not file_name:
        return "document"
    # Take basename only
    base_name = Path(file_name).name
    # Strip null bytes and control chars
    cleaned = "".join(c for c in base_name if c.isprintable() and c not in ("/", "\\", "\x00"))
    return cleaned or "document"


def validate_document_file(uploaded_file):
    """Validate uploaded document for size, extension, MIME type, binary header,

    path safety, macro prohibition, and decompression bombs.

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

    # 2. Extension & Path Traversal Validation
    raw_name = getattr(uploaded_file, "name", "")
    if ".." in raw_name or "/" in raw_name or "\\" in raw_name:
        # Check if user passed malicious traversal path
        if ".." in raw_name:
            raise ValidationError(
                {"file": "Nom de fichier invalide (tentative de traversée de chemin détectée)."}
            )

    extension = Path(raw_name).suffix.lower()
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
    initial_pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
    try:
        if signatures:
            header = uploaded_file.read(8)
            matches = any(header.startswith(sig) for sig in signatures)
            if not matches:
                raise ValidationError(
                    {
                        "file": (
                            f"Le contenu binaire du fichier ne correspond pas à l'extension {extension}."
                        )
                    }
                )

        # 5. Archive Safety (DOCX and PPTX are ZIP containers)
        if extension in (".docx", ".pptx"):
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(initial_pos)
            content = uploaded_file.read()

            if zipfile.is_zipfile(io.BytesIO(content)):
                try:
                    with zipfile.ZipFile(io.BytesIO(content)) as zf:
                        total_uncompressed = 0
                        for info in zf.infolist():
                            # Path traversal inside zip
                            if ".." in info.filename or info.filename.startswith(("/", "\\")):
                                raise ValidationError(
                                    {"file": "Structure d'archive malveillante détectée dans le document."}
                                )

                            # Prohibition of embedded macros or active executable components
                            if "vbaProject.bin" in info.filename.lower() or info.filename.endswith(
                                (".exe", ".vbs", ".bat", ".sh", ".cmd")
                            ):
                                raise ValidationError(
                                    {
                                        "file": (
                                            "Les documents contenant des macros VBA ou du code actif "
                                            "sont strictement interdits."
                                        )
                                    }
                                )

                            total_uncompressed += info.file_size

                        # Decompression bomb safeguard
                        if total_uncompressed > MAX_UNCOMPRESSED_ARCHIVE_BYTES:
                            raise ValidationError(
                                {"file": "Fichier archive rejeté : volume décompressé trop volumineux."}
                            )

                        compressed_size = max(1, len(content))
                        ratio = total_uncompressed / compressed_size
                        if ratio > MAX_DECOMPRESSION_RATIO and total_uncompressed > 10 * 1024 * 1024:
                            raise ValidationError(
                                {"file": "Ratio de compression anormalement élevé (protection zip bomb)."}
                            )
                except zipfile.BadZipFile as exc:
                    raise ValidationError(
                        {"file": f"Fichier {extension.upper()} corrompu ou archive invalide."}
                    ) from exc

    finally:
        # Always restore file stream position
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(initial_pos)

    return True
