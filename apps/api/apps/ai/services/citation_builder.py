from typing import Any


class CitationBuilder:
    """Constructs structured, verifiable citations preserving full provenance:

    document_id, page, chapter, section, chunk_id, and content snippet.
    """

    def build_citations(
        self, results: list[dict[str, Any]], snippet_length: int = 250
    ) -> list[dict[str, Any]]:
        citations = []
        for idx, item in enumerate(results):
            content = item.get("content", "").strip()
            snippet = content[:snippet_length] + ("..." if len(content) > snippet_length else "")

            page_val = item.get("page") or item.get("page_number")

            citation = {
                "citation_id": idx + 1,
                "chunk_id": str(item.get("chunk_id")),
                "document_id": str(item.get("document_id")),
                "document_title": item.get("document_title", "Document"),
                "page": page_val,
                "page_number": page_val,
                "chapter": item.get("chapter"),
                "section": item.get("section"),
                "subsection": item.get("subsection"),
                "snippet": snippet,
                "score": item.get("score"),
            }
            citations.append(citation)

        return citations

    def format_sources_summary(self, citations: list[dict[str, Any]]) -> str:
        """Formats citations into a clean markdown reference list."""
        if not citations:
            return "Aucune source documentée disponible."

        lines = ["### Sources documentaires :"]
        for c in citations:
            meta_parts = [f"**{c['document_title']}**"]
            if c.get("page"):
                meta_parts.append(f"Page {c['page']}")
            if c.get("chapter"):
                meta_parts.append(f"{c['chapter']}")
            if c.get("section"):
                meta_parts.append(f"{c['section']}")

            meta_str = " | ".join(meta_parts)
            lines.append(f"- **[{c['citation_id']}]** {meta_str}")
            if c.get("snippet"):
                lines.append(f"  > *« {c['snippet']} »*")

        return "\n".join(lines)
