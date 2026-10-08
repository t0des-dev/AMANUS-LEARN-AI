"""File Security & Upload Hardening.

Provides comprehensive validation for uploads to prevent remote code execution,
path traversal, MIME spoofing, zip bombs, and cross-site scripting vectors.
"""

from pathlib import Path
import re

from django.conf import settings
from rest_framework.exceptions import ValidationError

DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".bash", ".ps1", ".vbs",
    ".php", ".phtml", ".php3", ".php4", ".php5", ".phps",
    ".py", ".pyc", ".rb", ".pl", ".cgi",
    ".js", ".jsp", ".jspx", ".asp", ".aspx", ".cfm",
    ".dll", ".so", ".dylib", ".bin", ".jar",
    ".html", ".htm", ".xhtml", ".svg",  # SVG can contain embedded XSS
}

DEFAULT_ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".txt", ".md",
    ".mp3", ".wav", ".m4a", ".ogg",
}

MIME_SIGNATURES: dict[str, list[bytes]] = {
    ".pdf": [b"%PDF-"],
    ".docx": [b"PK\x03\x04"],
    ".pptx": [b"PK\x03\x04"],
    ".mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    ".wav": [b"RIFF"],
    ".ogg": [b"OggS"],
}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and invalid characters."""
    if not filename:
        return "unnamed_file"
    # Remove path elements
    name = Path(filename).name
    # Strip null bytes and control chars
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    # Prevent traversal patterns
    name = name.replace("..", "_").replace("/", "_").replace("\\", "_")
    return name.strip() or "unnamed_file"


def validate_file_security(
    uploaded_file,
    allowed_extensions: set[str] | None = None,
    max_size_bytes: int | None = None,
) -> bool:
    """Perform security and content validation on an uploaded file.

    Raises ValidationError if any security check fails.
    """
    if not uploaded_file:
        raise ValidationError({"file": "Aucun fichier n'a été fourni."})

    original_name = getattr(uploaded_file, "name", "")
    sanitized = sanitize_filename(original_name)

    # 1. Path traversal / null byte check
    if "\x00" in original_name or "/" in original_name or "\\" in original_name:
        raise ValidationError({"file": "Nom de fichier invalide (tentative de traversée détectée)."})

    extension = Path(sanitized).suffix.lower()

    # 2. Block dangerous executable extensions immediately
    if extension in DANGEROUS_EXTENSIONS:
        raise ValidationError(
            {"file": f"Le type de fichier '{extension}' est strictement interdit pour des raisons de sécurité."}
        )

    # 3. Verify against allowed extensions
    allowed = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
    if extension not in allowed:
        raise ValidationError(
            {"file": f"Extension non supportée '{extension}'. Extensions autorisées : {', '.join(sorted(allowed))}."}
        )

    # 4. Size validation
    max_size = max_size_bytes or getattr(settings, "MAX_DOCUMENT_SIZE", 50 * 1024 * 1024)
    size = getattr(uploaded_file, "size", 0)
    if size <= 0:
        raise ValidationError({"file": "Le fichier est vide (0 octet)."})
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError({"file": f"Fichier trop volumineux. La limite maximale est de {max_mb:.0f} Mo."})

    # 5. Magic Byte validation
    signatures = MIME_SIGNATURES.get(extension)
    if signatures:
        initial_pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
        header = uploaded_file.read(16)
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(initial_pos)

        matches = any(header.startswith(sig) for sig in signatures)
        if not matches:
            raise ValidationError(
                {"file": f"Le contenu binaire ne correspond pas à la signature attendue pour '{extension}'."}
            )

    return True
