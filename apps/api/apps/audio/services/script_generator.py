import re

from apps.courses.models import CourseSection


class PedagogicalScriptGenerator:
    """Transforms written course lessons into spoken, fluid pedagogical audio scripts.

    Cleans raw markdown, formulas, technical tags, and bullet lists,
    restructuring them into natural, conversational educational narratives
    in French, Arabic, or English.
    """

    I18N_TEMPLATES = {
        "fr": {
            "code_transition": " Voici l'extrait de code correspondant à cette notion. ",
            "intro": "Bonjour et bienvenue dans cette leçon audio intitulée : {title}.",
            "objectives": "Dans cet enregistrement, nos objectifs clés sont : {objectives}.",
            "bullets_prefix": "Retenons notamment : ",
            "bullets_join": ", puis : ",
            "default_content": "Cette leçon aborde les concepts fondamentaux de {title} tels que définis dans votre programme de cours.",
            "summary_prefix": "En synthèse de ce module : {summary}",
            "default_summary": "En résumé, retenez bien les notions clés présentées dans ce module sur {title}.",
            "outro": "Ceci conclut notre enregistrement audio. N'hésitez pas à réécouter cette capsule ou à passer au quiz d'entraînement.",
        },
        "ar": {
            "code_transition": " إليكم مقتطف الشيفرة البرمجية المرتبط بهذا المفهوم. ",
            "intro": "أهلاً ومرحباً بكم في هذا الدرس الصوتي بعنوان : {title}.",
            "objectives": "في هذا التسجيل، أهدافنا التعليمية الرئيسية هي : {objectives}.",
            "bullets_prefix": "نستحضر على وجه الخصوص : ",
            "bullets_join": "، ثم : ",
            "default_content": "يتناول هذا الدرس المفاهيم الجوهرية لموضوع {title} وفقاً لمقرركم التعليمي.",
            "summary_prefix": "في خلاصة هذا المحور : {summary}",
            "default_summary": "في الختام، احرصوا على ترسيخ النقاط الأساسية التي تم تناولها في {title}.",
            "outro": "بهذا نختتم تسجيلنا الصوتي. يمكنكم إعادة الاستماع إلى هذا المقطع أو الانتقال إلى اختبار التدريب.",
        },
        "en": {
            "code_transition": " Here is the code snippet related to this concept. ",
            "intro": "Hello and welcome to this audio lesson titled: {title}.",
            "objectives": "In this recording, our core learning objectives are: {objectives}.",
            "bullets_prefix": "Key takeaways include: ",
            "bullets_join": ", followed by: ",
            "default_content": "This lesson covers the foundational concepts of {title} as outlined in your curriculum.",
            "summary_prefix": "To summarize this module: {summary}",
            "default_summary": "In summary, keep in mind the central concepts covered in this module on {title}.",
            "outro": "This concludes our audio recording. Feel free to replay this track or proceed to the practice quiz.",
        },
    }

    def clean_markdown_for_speech(self, text: str, language: str = "fr") -> str:
        """Removes markdown formatting, brackets, URLs, and code blocks for spoken clarity."""
        if not text:
            return ""

        lang = language.lower() if language in self.I18N_TEMPLATES else "fr"
        code_rep = self.I18N_TEMPLATES[lang]["code_transition"]

        # Remove non-printable control characters (ASCII 0-31 except \n, \t)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Remove code blocks and replace with brief speech transition
        text = re.sub(r"```[\s\S]*?```", code_rep, text)

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
        language: str | None = None,
    ) -> str:
        """Generates an engaging, pedagogically structured spoken script from a CourseSection."""
        lang = (language or getattr(section.course, "language", None) or "fr").lower()
        if lang not in self.I18N_TEMPLATES:
            lang = "fr"
        i18n = self.I18N_TEMPLATES[lang]

        title = section.title or "cette section"
        raw_content = section.content or section.summary or ""
        cleaned_body = self.clean_markdown_for_speech(raw_content, language=lang)

        script_parts: list[str] = []

        # 1. Introduction
        script_parts.append(i18n["intro"].format(title=title))

        # Objectives mention if available
        if section.objectives and isinstance(section.objectives, list):
            valid_objs = [
                str(obj) if isinstance(obj, str) else obj.get("objective", "")
                for obj in section.objectives
                if obj
            ]
            if valid_objs:
                script_parts.append(i18n["objectives"].format(objectives=", ".join(valid_objs[:3])))

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
                    lines = [
                        line.replace("• ", "").strip()
                        for line in p_clean.split("\n")
                        if line.strip()
                    ]
                    trans_text = i18n["bullets_prefix"] + i18n["bullets_join"].join(lines) + "."
                    formatted_paragraphs.append(trans_text)
                else:
                    formatted_paragraphs.append(p_clean)

            script_parts.append("\n\n".join(formatted_paragraphs))
        else:
            script_parts.append(i18n["default_content"].format(title=title))

        # 3. Summary & Conclusion
        if section.summary and section.summary.strip():
            clean_summary = self.clean_markdown_for_speech(section.summary, language=lang)
            script_parts.append(i18n["summary_prefix"].format(summary=clean_summary))
        else:
            script_parts.append(i18n["default_summary"].format(title=title))

        script_parts.append(i18n["outro"])

        return "\n\n".join(script_parts)
