import logging
import re
from typing import Any

from apps.ai.models import GenerationType

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class SlideDeckGenerator(BaseGenerator):
    """Generates a RAG-grounded slide deck blueprint from a document.

    Produces the canonical AI payload ``{"slides": [{"slide_number", "title",
    "bullet_points", "speaker_notes"}]}`` consumed by the slides persistence
    layer (and expected by the evaluation harness).
    """

    generation_type = GenerationType.SLIDES

    def get_prompts(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
        slide_count: int | None = None,
        *args,
        **kwargs,
    ) -> tuple[str, str, str]:
        return self.prompt_service.get_slides_prompt(
            document_title=document_title,
            context=context,
            language=language,
            level=level,
            focus=focus,
            slide_count=slide_count,
        )

    @staticmethod
    def to_blueprints(
        result: Any,
        fallback_title: str = "",
        max_bullets: int = 6,
    ) -> list[dict[str, Any]]:
        """Converts the AI payload into persistence-ready slide blueprints.

        Returns a list of dicts shaped like the heuristic SlidePlanner output:
        ``{slide_number, slide_type, title, content, speaker_notes, image_prompt}``
        where ``content`` is the newline-joined, bullet-prefixed string the
        presentation models persist.
        """
        if not isinstance(result, dict):
            return []
        slides = result.get("slides")
        if not isinstance(slides, list):
            return []

        blueprints: list[dict[str, Any]] = []
        for raw in slides:
            if not isinstance(raw, dict):
                continue

            title = str(raw.get("title") or "").strip()
            if not title:
                title = fallback_title or f"Diapositive {len(blueprints) + 1}"

            bullets = raw.get("bullet_points") or []
            if isinstance(bullets, str):
                bullets = [bullets]
            cleaned: list[str] = []
            for bullet in bullets:
                text = SlideDeckGenerator._clean_bullet(str(bullet))
                if text and text not in cleaned:
                    cleaned.append(text)
                if len(cleaned) >= max_bullets:
                    break

            if not cleaned:
                continue

            notes = str(raw.get("speaker_notes") or "").strip()
            blueprints.append(
                {
                    "slide_number": len(blueprints) + 1,
                    "slide_type": "concept",
                    "title": title[:160],
                    "content": "\n".join(f"• {b}" for b in cleaned),
                    "speaker_notes": notes,
                    "image_prompt": f"Illustration pédagogique pour : {title[:100]}",
                }
            )

        return blueprints

    @staticmethod
    def _clean_bullet(text: str) -> str:
        """Strips markdown noise and caps bullet length."""
        if not text:
            return ""
        clean = re.sub(r"^[#\-*•0-9.)\s]+", "", text).strip()
        clean = re.sub(r"[*_`]", "", clean).strip()
        if clean.startswith("```"):
            return ""
        if len(clean) > 160:
            clean = clean[:160].rsplit(" ", 1)[0] + "..."
        return clean
