import logging
import re
from typing import Any

from apps.courses.models import Course, CourseSection

logger = logging.getLogger(__name__)


class SlidePlanner:
    """Plans pedagogical slide structure from a Course.

    Determines slide sequence, content summaries, speaker notes,
    and visual image prompts for each pedagogical step.
    """

    def plan_presentation(self, course: Course, title: str | None = None) -> list[dict[str, Any]]:
        """Generates a structured list of slide blueprints for the course."""
        sections = list(
            course.sections.filter(parent__isnull=True).order_by("order", "created_at")
        )
        # If no root chapters, use all sections
        if not sections:
            sections = list(course.sections.order_by("order", "created_at"))

        slides_plan: list[dict[str, Any]] = []
        slide_num = 1
        deck_title = (title or course.title).strip()

        # 1. Slide de Titre
        slides_plan.append(
            {
                "slide_number": slide_num,
                "slide_type": "title",
                "title": deck_title,
                "content": (
                    f"• Formation : {course.title}\n"
                    f"• Niveau : {course.get_level_display() if hasattr(course, 'get_level_display') else course.level}\n"
                    f"• Organisation : {course.organization.name}"
                ),
                "speaker_notes": (
                    f"Bienvenue à tous dans cette présentation consacrée à {course.title}. "
                    f"Ce cours s'adresse à un public de niveau {course.level}. "
                    "Nous allons parcourir ensemble les concepts clés et cas pratiques."
                ),
                "image_prompt": (
                    f"Modern educational banner illustration about {course.title}, "
                    "minimalist aesthetic, vibrant gradient, digital learning"
                ),
            }
        )
        slide_num += 1

        # 2. Slide d'Agenda / Sommaire
        agenda_points = []
        for idx, sec in enumerate(sections[:6]):
            agenda_points.append(f"• Module {idx + 1} : {sec.title}")

        if not agenda_points:
            agenda_points = [
                "• Module 1 : Fondements et principes théoriques",
                "• Module 2 : Mise en œuvre et cas pratiques",
                "• Module 3 : Synthèse et validation des compétences",
            ]

        slides_plan.append(
            {
                "slide_number": slide_num,
                "slide_type": "agenda",
                "title": "Sommaire & Objectifs du Cours",
                "content": "\n".join(agenda_points),
                "speaker_notes": (
                    "Voici la feuille de route de notre session. Nous allons aborder successivement "
                    "ces différents modules pour construire une maîtrise progressive et solide."
                ),
                "image_prompt": "Clean infographic roadmap with milestones, educational curriculum flowchart",
            }
        )
        slide_num += 1

        # 3. Slides de Contenu didactique pour chaque section
        for idx, sec in enumerate(sections):
            # Fetch children lessons if any
            children = list(sec.children.order_by("order", "created_at"))
            target_items = [sec] if not children else children[:4]

            for sub_item in target_items:
                clean_bullets = self._extract_key_bullets(sub_item)
                speaker_note = self._build_speaker_notes(sub_item)

                slides_plan.append(
                    {
                        "slide_number": slide_num,
                        "slide_type": "concept",
                        "title": sub_item.title,
                        "content": clean_bullets,
                        "speaker_notes": speaker_note,
                        "image_prompt": (
                            f"Conceptual visual diagram explaining {sub_item.title}, "
                            "clean vectors, professional presentation graphic"
                        ),
                    }
                )
                slide_num += 1

        # 4. Slide de Synthèse / Points Clés
        slides_plan.append(
            {
                "slide_number": slide_num,
                "slide_type": "summary",
                "title": "Synthèse & Points Clés à Retenir",
                "content": (
                    f"• Maîtrise des concepts fondamentaux de {course.title}\n"
                    "• Compréhension des mécanismes opérationnels et méthodologiques\n"
                    "• Capacité d'application autonome sur des cas réels\n"
                    "• Validation des acquis via les questionnaires d'évaluation"
                ),
                "speaker_notes": (
                    "Pour conclure, récapitulons les acquis essentiels. Assurez-vous de bien maîtriser "
                    "ces points pivots avant de passer aux exercices pratiques."
                ),
                "image_prompt": "Checklist icon with glowing validation badges, pedagogical achievement",
            }
        )
        slide_num += 1

        # 5. Slide de Conclusion & Questions / Réponses
        slides_plan.append(
            {
                "slide_number": slide_num,
                "slide_type": "conclusion",
                "title": "Conclusion & Questions / Réponses",
                "content": (
                    "• Merci pour votre attention et votre engagement !\n"
                    "• Place aux questions et échanges interactifs\n"
                    "• Retrouvez les ressources et fiches de révision sur la plateforme"
                ),
                "speaker_notes": (
                    "Merci à tous pour votre écoute. C'est le moment d'ouvrir la discussion : "
                    "avez-vous des questions sur les notions que nous venons d'explorer ?"
                ),
                "image_prompt": "Friendly Q&A speech bubbles, discussion icon, interactive workshop scene",
            }
        )

        return slides_plan

    def _extract_key_bullets(self, section: CourseSection) -> str:
        """Extracts 3 to 4 concise bullet points from a section."""
        bullets = []

        # Use objectives if present
        if section.objectives and isinstance(section.objectives, list):
            for obj in section.objectives[:3]:
                txt = str(obj) if isinstance(obj, str) else obj.get("objective", "")
                if txt.strip():
                    bullets.append(f"• {txt.strip()}")

        # Or extract from summary / content
        raw = section.summary or section.content or ""
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        for line in lines:
            if len(bullets) >= 4:
                break
            clean = re.sub(r"^[#\-*•0-9.)\s]+", "", line).strip()
            # Clean markdown tags
            clean = re.sub(r"[*_`]", "", clean).strip()
            if len(clean) > 15 and not clean.startswith("```"):
                bullets.append(f"• {clean[:120]}")

        if not bullets:
            bullets = [
                f"• Étude approfondie de la notion de {section.title}",
                "• Analyse des principes et règles méthodologiques",
                "• Mise en perspective dans le cadre applicatif du cours",
            ]

        return "\n".join(bullets[:4])

    def _build_speaker_notes(self, section: CourseSection) -> str:
        """Constructs explanatory speaking notes for the presenter."""
        if section.summary and len(section.summary) > 20:
            clean = re.sub(r"[*_#`]", "", section.summary).strip()
            return f"Dans cette diapositive sur {section.title} : {clean}"
        return (
            f"Prenez le temps d'expliquer chaque point de {section.title}. "
            "Donnez des exemples concrets pour ancrer la mémorisation chez les apprenants."
        )
