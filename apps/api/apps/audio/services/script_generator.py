import re
from typing import Any

from apps.courses.models import CourseSection


class PedagogicalScriptGenerator:
    """Transforms written course lessons into spoken, fluid pedagogical audio scripts.

    Cleans raw markdown, formulas, technical tags, and bullet lists,
    restructuring them into natural, conversational educational narratives.
    """

    def clean_markdown_for_speech(self, text: str) -> str:
        """Removes markdown formatting, brackets, URLs, and code blocks for spoken clarity."""
        if not text:
            return ""

        # Remove code blocks and replace with brief speech transition
        text = re.sub(
            r"```[\s\S]*?```",
            " Voici l'extrait de code correspondant à cette notion. ",
            text,
        )

        # Remove inline code `...`
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove markdown headers #, ##, ###
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Remove images ![alt](url) and links [text](url)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)

        # Remove citation brackets like [1], [2], etc.
        text = re.sub(r"\[\d+\]", "", text)

        # Remove bold/italic markers **text** or *text*
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # Convert bullet points into conversational pauses
        text = re.sub(r"^\s*[-*•]\s+", "• ", text, flags=re.MULTILINE)

        # Clean multiple spaces and newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def generate_script(
        self,
        section: CourseSection,
        custom_instructions: str | None = None,
    ) -> str:
        """Generates an engaging, pedagogically structured spoken script from a CourseSection."""
        title = section.title or "cette section"
        raw_content = section.content or section.summary or ""
        cleaned_body = self.clean_markdown_for_speech(raw_content)

        script_parts: list[str] = []

        # 1. Introduction
        script_parts.append(
            f"Bonjour et bienvenue dans cette leçon audio intitulée : {title}."
        )

        # Objectives mention if available
        if section.objectives and isinstance(section.objectives, list):
            valid_objs = [
                str(obj) if isinstance(obj, str) else obj.get("objective", "")
                for obj in section.objectives
                if obj
            ]
            if valid_objs:
                script_parts.append(
                    "Dans cet enregistrement, nos objectifs clés sont : "
                    + ", ".join(valid_objs[:3])
                    + "."
                )

        # 2. Main Lesson Content
        if cleaned_body:
            # Format bullets into spoken transitions
            paragraphs = cleaned_body.split("\n\n")
            formatted_paragraphs = []
            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean:
                    continue
                if p_clean.startswith("• "):
                    lines = [line.replace("• ", "").strip() for line in p_clean.split("\n") if line.strip()]
                    trans_text = "Retenons notamment : " + ", puis : ".join(lines) + "."
                    formatted_paragraphs.append(trans_text)
                else:
                    formatted_paragraphs.append(p_clean)

            script_parts.append("\n\n".join(formatted_paragraphs))
        else:
            script_parts.append(
                f"Cette leçon aborde les concepts fondamentaux de {title} tels que définis dans votre programme de cours."
            )

        # 3. Summary & Conclusion
        if section.summary and section.summary.strip():
            clean_summary = self.clean_markdown_for_speech(section.summary)
            script_parts.append(
                f"En synthèse de ce module : {clean_summary}"
            )
        else:
            script_parts.append(
                f"En résumé, retenez bien les notions clés présentées dans ce module sur {title}."
            )

        script_parts.append(
            "Ceci conclut notre enregistrement audio. N'hésitez pas à réécouter cette capsule ou à passer au quiz d'entraînement."
        )

        return "\n\n".join(script_parts)
