import logging
import re
from typing import Any

from apps.courses.models import Course, CourseSection
from apps.slides.services.validator import PresentationValidator

logger = logging.getLogger(__name__)


class SlidePlanner:
    """Plans pedagogical slide deck structure from a Course.

    Supports French (fr), Arabic (ar), and English (en) with level adaptation,
    concise pedagogical bullet extraction, dynamic two-column layouts,
    rich presenter notes, and image prompts.
    """

    I18N_BLUEPRINTS = {
        "fr": {
            "course_label": "Formation",
            "level_label": "Niveau",
            "org_label": "Organisation",
            "agenda_title": "Sommaire & Objectifs du Cours",
            "module_prefix": "Module",
            "summary_title": "Synthèse & Points Clés à Retenir",
            "conclusion_title": "Conclusion & Questions / Réponses",
            "default_agenda": [
                "• Module 1 : Fondements et principes théoriques",
                "• Module 2 : Mise en œuvre et cas pratiques",
                "• Module 3 : Synthèse et validation des compétences",
            ],
            "default_summary": (
                "• Maîtrise des concepts fondamentaux du programme\n"
                "• Compréhension des mécanismes opérationnels et méthodologiques\n"
                "• Capacité d'application autonome sur des cas concrets\n"
                "• Validation des compétences acquises"
            ),
            "default_conclusion": (
                "• Merci pour votre attention et votre engagement !\n"
                "• Place aux questions et échanges interactifs\n"
                "• Retrouvez les ressources et fiches de révision sur la plateforme"
            ),
            "welcome_notes": (
                "Bienvenue à tous dans cette présentation consacrée à {title}. "
                "Ce support s'adresse à un public de niveau {level}. "
                "Nous allons parcourir ensemble les concepts clés et cas pratiques."
            ),
            "agenda_notes": (
                "Voici la feuille de route de notre session. Nous allons aborder successivement "
                "ces différents axes pour construire une compréhension solide et progressive."
            ),
            "summary_notes": (
                "Pour conclure, récapitulons les acquis essentiels. Assurez-vous de bien maîtriser "
                "ces points pivots avant de passer aux exercices d'application."
            ),
            "conclusion_notes": (
                "Merci à tous pour votre écoute. C'est le moment d'ouvrir la discussion : "
                "avez-vous des questions sur les notions que nous venons d'explorer ?"
            ),
        },
        "ar": {
            "course_label": "المقرر التعليمي",
            "level_label": "المستوى",
            "org_label": "المؤسسة",
            "agenda_title": "جدول الأعمال والأهداف التعليمية",
            "module_prefix": "المحور",
            "summary_title": "الخلاصة والنقاط الجوهرية",
            "conclusion_title": "الخاتمة والأسئلة والأجوبة",
            "default_agenda": [
                "• المحور 1 : الأسس النظرية والمفاهيم الجوهرية",
                "• المحور 2 : التطبيقات الميدانية ودراسة الحالات",
                "• المحور 3 : التقييم الشامل وترسيخ المكتسبات",
            ],
            "default_summary": (
                "• استيعاب الأسس والقواعد المنهجية الرئيسية\n"
                "• فهم آليات التطبيق والتحليل العملي\n"
                "• القدرة على التوظيف الذاتي في السياقات الواقعية\n"
                "• تقييم المعارف المكتسبة وتثبيتها"
            ),
            "default_conclusion": (
                "• شكراً جزيلاً لحسن متابعتكم واهتمامكم !\n"
                "• نفتح الآن المجال لطرح الأسئلة والنقاش التفاعلي\n"
                "• الموارد وبطاقات المراجعة متاحة عبر المنصة التعليمية"
            ),
            "welcome_notes": (
                "أهلاً بكم جميعاً في هذا العرض التعليمي المخصص لمقرر {title}. "
                "هذا المحتوى موجه لمستوى {level}. "
                "سنستعرض معاً أهم المفاهيم والتطبيقات العملية خطوة بخطوة."
            ),
            "agenda_notes": (
                "إليكم محاور جلستنا التعليمية. سنتناول بالتسلسل "
                "هذه الموضوعات لضمان اكتساب تدريجي ومتين للمهارات."
            ),
            "summary_notes": (
                "في ختام هذا العرض، نلخص أهم الركائز التي تم تناولها. "
                "احرصوا على مراجعة هذه المفاهيم الأساسية قبل الانتقال للتمارين."
            ),
            "conclusion_notes": (
                "شكراً لمشاركتكم. المجال مفتوح الآن لنقاش أي استفسار أو نقطة تودون التوسع فيها."
            ),
        },
        "en": {
            "course_label": "Course",
            "level_label": "Level",
            "org_label": "Organization",
            "agenda_title": "Agenda & Learning Objectives",
            "module_prefix": "Module",
            "summary_title": "Key Takeaways & Summary",
            "conclusion_title": "Conclusion & Q&A Session",
            "default_agenda": [
                "• Module 1: Theoretical Foundations and Core Principles",
                "• Module 2: Practical Implementation and Case Studies",
                "• Module 3: Summary and Competency Assessment",
            ],
            "default_summary": (
                "• Mastery of fundamental concepts and frameworks\n"
                "• Clear understanding of operational mechanisms\n"
                "• Independent application to real-world scenarios\n"
                "• Knowledge validation and progress checkpoints"
            ),
            "default_conclusion": (
                "• Thank you for your attention and engagement!\n"
                "• Questions, thoughts, and interactive discussion\n"
                "• Additional resources and revision sheets available on platform"
            ),
            "welcome_notes": (
                "Welcome everyone to this presentation on {title}. "
                "Designed for {level} learners, this session guides you through "
                "core pedagogical concepts and concrete applications."
            ),
            "agenda_notes": (
                "Here is our roadmap for today. We will progress step-by-step "
                "through each module to build deep understanding."
            ),
            "summary_notes": (
                "To wrap up, let's review our central takeaways. "
                "Make sure these core principles are clear before practical exercises."
            ),
            "conclusion_notes": (
                "Thank you all for participating. The floor is now open for questions "
                "and interactive discussion."
            ),
        },
    }

    def plan_presentation(
        self,
        course: Course,
        title: str | None = None,
        language: str | None = None,
        level: str | None = None,
        focus: str | None = None,
        target_slides_count: int | None = None,
    ) -> list[dict[str, Any]]:
        """Generates a structured list of slide blueprints for the course."""
        lang = (language or getattr(course, "language", None) or "fr").lower()
        if lang not in self.I18N_BLUEPRINTS:
            lang = "fr"
        i18n = self.I18N_BLUEPRINTS[lang]

        effective_level = level or getattr(course, "level", "BEGINNER")
        deck_title = (title or course.title).strip()
        org_name = course.organization.name if course.organization else "Amanus Learn AI"

        sections = list(course.sections.filter(parent__isnull=True).order_by("order", "created_at"))
        if not sections:
            sections = list(course.sections.order_by("order", "created_at"))

        slides_plan: list[dict[str, Any]] = []
        slide_num = 1

        # 1. Title / Cover Slide
        title_content = (
            f"• {i18n['course_label']} : {course.title}\n"
            f"• {i18n['level_label']} : {effective_level}\n"
            f"• {i18n['org_label']} : {org_name}"
        )
        slides_plan.append(
            {
                "slide_number": slide_num,
                "slide_type": "title",
                "title": deck_title,
                "content": title_content,
                "speaker_notes": i18n["welcome_notes"].format(
                    title=deck_title, level=effective_level
                ),
                "image_prompt": f"Modern educational banner illustration for {deck_title}, professional graphic design",
            }
        )
        slide_num += 1

        # 2. Agenda / Roadmap Slide
        agenda_points = []
        for idx, sec in enumerate(sections[:6]):
            agenda_points.append(f"• {i18n['module_prefix']} {idx + 1} : {sec.title}")

        if not agenda_points:
            agenda_points = i18n["default_agenda"]

        slides_plan.append(
            {
                "slide_number": slide_num,
                "slide_type": "agenda",
                "title": i18n["agenda_title"],
                "content": "\n".join(agenda_points),
                "speaker_notes": i18n["agenda_notes"],
                "image_prompt": "Clean infographic roadmap with numbered milestones, curriculum flowchart",
            }
        )
        slide_num += 1

        # 3. Content Slides per Section / Chapter
        for sec_idx, sec in enumerate(sections):
            children = list(sec.children.order_by("order", "created_at"))
            target_items = [sec] if not children else children[:4]

            for item_idx, sub_item in enumerate(target_items):
                bullets, is_two_col = self._extract_key_bullets(sub_item, lang=lang)
                speaker_note = self._build_speaker_notes(sub_item, lang=lang)

                slide_type = "two_column" if is_two_col else "concept"
                item_title = sub_item.title.strip()
                if not item_title:
                    item_title = f"{i18n['module_prefix']} {sec_idx + 1}.{item_idx + 1}"

                validated_slide = PresentationValidator.validate_slide_content(
                    title=item_title,
                    content=bullets,
                    slide_number=slide_num,
                )

                slides_plan.append(
                    {
                        "slide_number": slide_num,
                        "slide_type": slide_type,
                        "title": validated_slide["title"],
                        "content": validated_slide["content"],
                        "speaker_notes": speaker_note,
                        "image_prompt": f"Conceptual visual diagram explaining {item_title}, clean vectors",
                    }
                )
                slide_num += 1

        # 4. Summary / Key Points Slide
        summary_content = i18n["default_summary"]
        if focus:
            summary_content += f"\n• Focus : {focus}"

        slides_plan.append(
            {
                "slide_number": slide_num,
                "slide_type": "summary",
                "title": i18n["summary_title"],
                "content": summary_content,
                "speaker_notes": i18n["summary_notes"],
                "image_prompt": "Checklist icon with glowing validation badges, pedagogical achievement",
            }
        )
        slide_num += 1

        # 5. Conclusion & Q&A Slide
        slides_plan.append(
            {
                "slide_number": slide_num,
                "slide_type": "conclusion",
                "title": i18n["conclusion_title"],
                "content": i18n["default_conclusion"],
                "speaker_notes": i18n["conclusion_notes"],
                "image_prompt": "Friendly Q&A speech bubbles, discussion icon, interactive workshop scene",
            }
        )

        return slides_plan

    def _extract_key_bullets(self, section: CourseSection, lang: str = "fr") -> tuple[str, bool]:
        """Extracts 3 to 4 concise bullet points from a section.

        Returns:
            (formatted_content_string, is_two_column_candidate)
        """
        bullets: list[str] = []

        # 1. Use explicit objectives if present
        if section.objectives and isinstance(section.objectives, list):
            for obj in section.objectives[:3]:
                txt = str(obj) if isinstance(obj, str) else obj.get("objective", "")
                clean_txt = self._clean_text_bullet(txt)
                if clean_txt:
                    bullets.append(clean_txt)

        # 2. Extract from summary or content
        raw = section.summary or section.content or ""
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        for line in lines:
            if len(bullets) >= 4:
                break
            clean = self._clean_text_bullet(line)
            if clean and clean not in bullets and len(clean) >= 12:
                bullets.append(clean)

        # Fallback default bullets if section content was sparse
        if not bullets:
            if lang == "ar":
                bullets = [
                    f"دراسة مستفيضة لمفهوم {section.title}",
                    "تحليل القواعد والأسس المنهجية المتبعة",
                    "التطبيق العملي في السياق التعليمي للمقرر",
                ]
            elif lang == "en":
                bullets = [
                    f"Comprehensive study of {section.title}",
                    "Analysis of core principles and methodology",
                    "Practical application within course framework",
                ]
            else:
                bullets = [
                    f"Étude approfondie de la notion de {section.title}",
                    "Analyse des principes et règles méthodologiques",
                    "Mise en perspective dans le cadre applicatif du cours",
                ]

        # Check if suitable for two-column split (e.g. 4 distinct points)
        is_two_col = len(bullets) >= 4
        if is_two_col:
            # Format with delimiter ' || ' for left vs right column rendering
            mid = len(bullets) // 2
            left_part = "\n".join(f"• {b}" for b in bullets[:mid])
            right_part = "\n".join(f"• {b}" for b in bullets[mid:])
            return f"{left_part}\n || \n{right_part}", True

        return "\n".join(f"• {b}" for b in bullets[:4]), False

    def _clean_text_bullet(self, text: str) -> str:
        """Strips markdown tags, list prefixes, and normalizes length."""
        if not text:
            return ""
        clean = re.sub(r"^[#\-*•0-9.)\s]+", "", text).strip()
        clean = re.sub(r"[*_`]", "", clean).strip()
        if clean.startswith("```"):
            return ""
        if len(clean) > 120:
            clean = clean[:120].rsplit(" ", 1)[0] + "..."
        return clean

    def _build_speaker_notes(self, section: CourseSection, lang: str = "fr") -> str:
        """Constructs explanatory speaking notes for the presenter."""
        if section.summary and len(section.summary.strip()) > 20:
            clean = re.sub(r"[*_#`]", "", section.summary).strip()
            if lang == "ar":
                return f"في هذه الشريحة حول {section.title} : {clean}"
            elif lang == "en":
                return f"In this slide covering {section.title}: {clean}"
            return f"Dans cette diapositive sur {section.title} : {clean}"

        if lang == "ar":
            return (
                f"ركز على شرح كل نقطة من نقاط {section.title} بدقة. "
                "قدّم أمثلة واقعية لتيسير استيعاب المفاهيم لدى الطلاب."
            )
        elif lang == "en":
            return (
                f"Take time to explain each point of {section.title}. "
                "Provide practical examples to anchor understanding for learners."
            )
        return (
            f"Prenez le temps d'expliquer chaque point de {section.title}. "
            "Donnez des exemples concrets pour ancrer la mémorisation chez les apprenants."
        )
