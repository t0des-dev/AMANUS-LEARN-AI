from typing import Any


class ContextBuilder:
    """Constructs prompt-ready contextual blocks from retrieved and re-ranked chunks.

    Enforces strict grounding and source referencing to prevent AI hallucinations.
    """

    def __init__(self, max_context_chars: int = 12000):
        self.max_context_chars = max_context_chars

    def build_context(self, results: list[dict[str, Any]]) -> str:
        """Assembles structured context blocks from retrieved chunks."""
        if not results:
            return ""

        blocks = []
        total_len = 0

        for idx, item in enumerate(results):
            source_num = idx + 1
            doc_title = item.get("document_title", "Document")
            doc_id = item.get("document_id")
            page = item.get("page") or item.get("page_number")
            chapter = item.get("chapter")
            section = item.get("section")
            content = item.get("content", "").strip()

            header_parts = [f"Source [{source_num}] : {doc_title} (ID: {doc_id})"]
            if page:
                header_parts.append(f"Page: {page}")
            if chapter:
                header_parts.append(f"Chapitre: {chapter}")
            if section:
                header_parts.append(f"Section: {section}")

            header_line = " | ".join(header_parts)
            block = f"--- {header_line} ---\n{content}\n"

            if total_len + len(block) > self.max_context_chars and blocks:
                break

            blocks.append(block)
            total_len += len(block)

        return "\n".join(blocks).strip()

    def build_rag_prompt(self, query: str, context: str) -> str:
        """Assembles prompt payload with strict anti-hallucination instructions."""
        anti_hallucination_rule = (
            "Consignes strictes : Répondez à la question en vous basant EXCLUSIVEMENT sur les "
            "sources fournies ci-dessus. Citez systématiquement vos sources sous la forme [1], [2], etc. "
            "Si l'information n'est pas présente dans les sources, répondez exactement : "
            "« Cette information n'est pas présente dans les documents disponibles. »"
        )

        if not context:
            return (
                f"Question : {query}\n\n"
                f"Aucun document pertinent trouvé dans l'organisation.\n\n"
                f"{anti_hallucination_rule}"
            )

        return (
            f"Contexte documentaire extrait :\n\n"
            f"{context}\n\n"
            f"Question de l'utilisateur : {query}\n\n"
            f"{anti_hallucination_rule}"
        )
