import logging
from datetime import datetime, timezone
from typing import Any

from celery import shared_task
from django.db import transaction

from apps.documents.models import Document, DocumentStatus
from apps.documents.services.storage import get_storage_service
from apps.ingestion.models import DocumentPage
from apps.ingestion.parsers import DocumentParserFactory
from apps.ingestion.services.chunking import ChunkingService

logger = logging.getLogger(__name__)


def extract_document(document_id: str) -> dict[str, Any]:
    """Step 1 & 2: Extract text, perform OCR if needed, normalize, and detect structure."""
    document = Document.objects.get(id=document_id)

    document.status = DocumentStatus.EXTRACTING
    document.error_message = ""
    document.save(update_fields=["status", "error_message", "updated_at"])

    storage = get_storage_service()
    if not storage.file_exists(document.storage_key):
        raise FileNotFoundError(f"Fichier introuvable dans le stockage : {document.storage_key}")

    file_stream = storage.get_file(document.storage_key)
    file_bytes = file_stream.read()

    # Step: File Detection and Parser Selection
    parser = DocumentParserFactory.get_parser(document.file_type)

    logger.info(f"[Ingestion] Parsing document {document.id} using {parser.__class__.__name__}")
    parsed_doc = parser.parse(file_bytes)

    # Check if OCR was used across any page
    any_ocr = any(p.ocr_used for p in parsed_doc.pages)
    if any_ocr:
        document.status = DocumentStatus.OCR
        document.save(update_fields=["status", "updated_at"])

    # Step: Structuring & Persistence
    document.status = DocumentStatus.STRUCTURING
    document.save(update_fields=["status", "updated_at"])

    with transaction.atomic():
        # Clear previous pages if re-extracting
        DocumentPage.objects.filter(document=document).delete()

        pages_to_create = []
        for p in parsed_doc.pages:
            pages_to_create.append(
                DocumentPage(
                    document=document,
                    page_number=p.page_number,
                    text=p.text,
                    ocr_used=p.ocr_used,
                    metadata=p.metadata,
                )
            )

        if pages_to_create:
            DocumentPage.objects.bulk_create(pages_to_create)

        document.page_count = len(pages_to_create)
        document.save(update_fields=["page_count", "updated_at"])

    logger.info(f"[Ingestion] Extracted {len(pages_to_create)} pages for document {document.id}")
    return {
        "status": "extracted",
        "document_id": str(document.id),
        "pages_count": len(pages_to_create),
        "ocr_used": any_ocr,
    }


def create_chunks(document_id: str) -> dict[str, Any]:
    """Step 3: Perform semantic chunking preserving document, page, chapter, section, subsection."""
    document = Document.objects.get(id=document_id)

    document.status = DocumentStatus.CHUNKING
    document.save(update_fields=["status", "updated_at"])

    chunker = ChunkingService()
    chunks = chunker.create_chunks_for_document(document)

    logger.info(f"[Ingestion] Created {len(chunks)} chunks for document {document.id}")
    return {
        "status": "chunked",
        "document_id": str(document.id),
        "chunks_count": len(chunks),
    }


@shared_task(bind=True, queue="heavy", max_retries=3, default_retry_delay=10)
def process_document(self, document_id: str) -> dict[str, Any]:
    """Celery background pipeline orchestrating the complete ingestion lifecycle.

    Lifecycle progression:
    UPLOADED -> EXTRACTING -> [OCR] -> STRUCTURING -> CHUNKING -> COMPLETED
    """
    logger.info(f"[Ingestion Pipeline] Initiating processing for document ID: {document_id}")

    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"[Ingestion Pipeline] Document not found: {document_id}")
        return {"status": "failed", "error": f"Document {document_id} introuvable."}

    try:
        # Phase 1: Extraction & Structuring
        extract_result = extract_document(str(document.id))

        # Phase 2: Chunking
        chunk_result = create_chunks(str(document.id))

        document.refresh_from_db()
        document.status = DocumentStatus.READY
        document.error_message = ""
        document.processing_metadata = {
            "progress_stage": "Completed",
            "pages_count": extract_result.get("pages_count", 0),
            "chunks_count": chunk_result.get("chunks_count", 0),
            "ocr_used": extract_result.get("ocr_used", False),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        document.save(
            update_fields=["status", "error_message", "processing_metadata", "updated_at"]
        )

        logger.info(
            f"[Ingestion Pipeline] Document {document_id} ingestion completed successfully. "
            f"Pages: {extract_result.get('pages_count')}, Chunks: {chunk_result.get('chunks_count')}"
        )

        return {
            "status": "completed",
            "document_id": str(document.id),
            "pages_count": extract_result.get("pages_count"),
            "chunks_count": chunk_result.get("chunks_count"),
        }

    except Exception as exc:
        logger.exception(
            f"[Ingestion Pipeline] Error during document processing {document_id}: {exc}"
        )
        document.refresh_from_db()
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)
        document.save(update_fields=["status", "error_message", "updated_at"])
        return {
            "status": "failed",
            "document_id": str(document.id),
            "error": str(exc),
        }
