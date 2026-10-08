import re
from typing import Any


def tokenize_query(text: str) -> set[str]:
    """Extracts lowercase alpha-numeric keywords from text (ignoring short stopwords)."""
    words = re.findall(r"\b\w{3,}\b", text.lower())
    stopwords = {
        "les",
        "des",
        "une",
        "dans",
        "pour",
        "par",
        "avec",
        "sur",
        "est",
        "sont",
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "what",
        "which",
    }
    return {w for w in words if w not in stopwords}


class Reranker:
    """Re-ranks vector candidate chunks using hybrid lexical relevance and structural heading boosts."""

    def __init__(self, vector_weight: float = 0.7, lexical_weight: float = 0.3):
        self.vector_weight = vector_weight
        self.lexical_weight = lexical_weight

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []

        query_tokens = tokenize_query(query)
        if not query_tokens:
            return candidates[:top_k]

        reranked = []

        for cand in candidates:
            content = cand.get("content", "").lower()
            chapter = str(cand.get("chapter") or "").lower()
            section = str(cand.get("section") or "").lower()

            # Lexical overlap score
            matched_tokens = sum(1 for tok in query_tokens if tok in content)
            lexical_ratio = matched_tokens / len(query_tokens)

            # Structural heading boost: if query tokens appear in chapter or section title
            heading_boost = 0.0
            for tok in query_tokens:
                if tok in chapter or tok in section:
                    heading_boost += 0.15

            lexical_score = min(1.0, lexical_ratio + heading_boost)
            vector_score = float(cand.get("score", 0.0))

            final_score = (self.vector_weight * vector_score) + (
                self.lexical_weight * lexical_score
            )

            updated = dict(cand)
            updated["score"] = round(final_score, 4)
            updated["vector_score"] = vector_score
            updated["lexical_score"] = round(lexical_score, 4)
            reranked.append(updated)

        # Sort descending by re-ranked score
        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked[:top_k]
