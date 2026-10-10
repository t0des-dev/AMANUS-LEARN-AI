import logging
import re
from typing import Any

from django.db import transaction

from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.ingestion.parsers.normalization import normalize_text
from apps.ingestion.parsers.structure_detector import detect_structure

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service responsible for semantic, hierarchical text chunking.

    Preserves document, page, chapter, section, and subsection metadata.
    Implements sliding window overlap for continuous semantic context in RAG.
    """

    def __init__(
        self,
        target_tokens: int = 500,
        overlap_tokens: int = 50,
        chars_per_token: float = 4.0,
    ):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.chars_per_token = chars_per_token
        self.target_chars = int(target_tokens * chars_per_token)
        self.overlap_chars = int(overlap_tokens * chars_per_token)

    def estimate_tokens(self, text: str) -> int:
        """Estimates token count using character and whitespace heuristics."""
        if not text:
            return 0
        words = len(text.split())
        char_estimate = len(text) / self.chars_per_token
        # Robust blended estimate
        return max(1, int((words * 1.33 + char_estimate) / 2))

    def split_into_semantic_units(self, text: str) -> list[str]:
        """Splits text into paragraphs, then sentences if necessary."""
        clean = normalize_text(text)
        if not clean:
            return []

        # Split on double newlines (paragraphs)
        paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
        units: list[str] = []

        for p in paragraphs:
            if len(p) <= self.target_chars:
                units.append(p)
            else:
                # Split large paragraphs into sentences
                sentences = re.split(r"(?<=[.!?])\s+", p)
                current_sub = ""
                for s in sentences:
                    if len(current_sub) + len(s) + 1 <= self.target_chars:
                        current_sub = f"{current_sub} {s}".strip() if current_sub else s
                    else:
                        if current_sub:
                            units.append(current_sub)
                        current_sub = s
                if current_sub:
                    units.append(current_sub)

        return units

    def chunk_page_content(
        self,
        page: DocumentPage,
        base_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Produces raw chunk data dictionaries for a given DocumentPage."""
        text = page.text.strip()
        if not text:
            return []

        page_meta = page.metadata or {}
        active_chapter = page_meta.get("chapter") or base_metadata.get("chapter")
        active_section = page_meta.get("section") or base_metadata.get("section")
        active_subsection = page_meta.get("subsection") or base_metadata.get("subsection")

        units = self.split_into_semantic_units(text)
        if not units:
            return []

        chunks_data: list[dict[str, Any]] = []
        current_chunk_blocks: list[str] = []
        current_length = 0

        for unit in units:
            unit_struct = detect_structure(unit)
            if unit_struct.get("chapter"):
                active_chapter = unit_struct["chapter"]
            if unit_struct.get("section"):
                active_section = unit_struct["section"]
            if unit_struct.get("subsection"):
                active_subsection = unit_struct["subsection"]

            unit_len = len(unit)

            if current_length + unit_len > self.target_chars and current_chunk_blocks:
                content = "\n\n".join(current_chunk_blocks).strip()
                chunks_data.append(
                    {
                        "content": content,
                        "token_count": self.estimate_tokens(content),
                        "page": page,
                        "chapter": active_chapter,
                        "section": active_section,
                        "subsection": active_subsection,
                    }
                )

                # Maintain overlap from trailing content
                overlap_blocks: list[str] = []
                overlap_len = 0
                for block in reversed(current_chunk_blocks):
                    if overlap_len + len(block) <= self.overlap_chars:
                        overlap_blocks.insert(0, block)
                        overlap_len += len(block)
                    else:
                        break

                current_chunk_blocks = overlap_blocks + [unit]
                current_length = sum(len(b) for b in current_chunk_blocks)
            else:
                current_chunk_blocks.append(unit)
                current_length += unit_len

        if current_chunk_blocks:
            content = "\n\n".join(current_chunk_blocks).strip()
            chunks_data.append(
                {
                    "content": content,
                    "token_count": self.estimate_tokens(content),
                    "page": page,
                    "chapter": active_chapter,
                    "section": active_section,
                    "subsection": active_subsection,
                }
            )

        return chunks_data

    @transaction.atomic
    def create_chunks_for_document(self, document) -> list[DocumentChunk]:
        """Creates and persists DocumentChunk models for an entire document."""
        # Purge existing chunks if re-processing to maintain idempotency
        DocumentChunk.objects.filter(document=document).delete()

        pages = list(document.pages.all().order_by("page_number"))
        if not pages:
            logger.warning(f"[ChunkingService] No pages found for document {document.id}")
            return []

        all_chunks: list[DocumentChunk] = []
        chunk_idx = 0

        running_chapter: str | None = None
        running_section: str | None = None
        running_subsection: str | None = None

        for page in pages:
            context = {
                "chapter": running_chapter,
                "section": running_section,
                "subsection": running_subsection,
            }

            page_chunks_data = self.chunk_page_content(page, context)

            for chunk_dict in page_chunks_data:
                running_chapter = chunk_dict.get("chapter") or running_chapter
                running_section = chunk_dict.get("section") or running_section
                running_subsection = chunk_dict.get("subsection") or running_subsection

                import hashlib

                content_hash = hashlib.sha256(chunk_dict["content"].encode("utf-8")).hexdigest()
                chunk_meta = {
                    "document_id": str(document.id),
                    "document_title": document.title,
                    "page_number": page.page_number,
                    "chapter": chunk_dict.get("chapter") or running_chapter,
                    "section": chunk_dict.get("section") or running_section,
                    "subsection": chunk_dict.get("subsection") or running_subsection,
                    "chunk_index": chunk_idx,
                    "char_count": len(chunk_dict["content"]),
                    "content_hash": content_hash,
                }

                chunk_obj = DocumentChunk(
                    document=document,
                    page=page,
                    chunk_index=chunk_idx,
                    content=chunk_dict["content"],
                    token_count=chunk_dict["token_count"],
                    metadata=chunk_meta,
                )
                all_chunks.append(chunk_obj)
                chunk_idx += 1

        if all_chunks:
            embedding_model_name = "unknown"
            embedding_dim = 1536
            try:
                from datetime import datetime, timezone

                from apps.ai.services.embeddings import get_embedding_provider

                provider = get_embedding_provider()
                embedding_model_name = provider.model_name
                embedding_dim = provider.dimensions

                contents = [c.content for c in all_chunks]
                embeddings = provider.embed_batch(contents)
                for chunk, emb in zip(all_chunks, embeddings):
                    chunk.embedding = emb
                    if isinstance(chunk.metadata, dict):
                        chunk.metadata["embedding_model"] = embedding_model_name
                        chunk.metadata["embedding_dim"] = embedding_dim

                # Update document index status
                doc_meta = document.processing_metadata or {}
                doc_meta["index_status"] = "INDEXED"
                doc_meta["embedding_model"] = embedding_model_name
                doc_meta["embedding_dim"] = embedding_dim
                doc_meta["indexed_at"] = datetime.now(timezone.utc).isoformat()
                document.processing_metadata = doc_meta
                document.save(update_fields=["processing_metadata", "updated_at"])
            except Exception as e:
                logger.warning(f"[ChunkingService] Could not generate embeddings: {e}")

            DocumentChunk.objects.bulk_create(all_chunks)

        # Invalidate RAG cache for this document and tenant
        try:
            from apps.ai.services.retriever import Retriever

            Retriever.invalidate_cache(str(document.organization_id), str(document.id))
        except Exception as e:
            logger.warning(f"[ChunkingService] Could not invalidate RAG cache: {e}")

        logger.info(
            f"[ChunkingService] Successfully generated {len(all_chunks)} chunks "
            f"for document {document.id} across {len(pages)} pages."
        )
        return all_chunks
