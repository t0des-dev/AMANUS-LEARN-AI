import io
import logging
import re
from typing import Any

from pptx import Presentation as PptxPresentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from apps.documents.services.storage import get_storage_service
from apps.slides.models import (
    Presentation,
    PresentationSlide,
    PresentationStatus,
    PresentationTheme,
)
from apps.slides.services.validator import PresentationValidator

logger = logging.getLogger(__name__)

# Color palettes per theme
THEME_PALETTES: dict[str, dict[str, RGBColor]] = {
    PresentationTheme.MODERN_DARK: {
        "bg": RGBColor(15, 23, 42),  # Slate-900
        "card_bg": RGBColor(30, 41, 59),  # Slate-800
        "card_border": RGBColor(51, 65, 85),  # Slate-700
        "title": RGBColor(248, 250, 252),  # Slate-50
        "subtitle": RGBColor(148, 163, 184),  # Slate-400
        "text": RGBColor(226, 232, 240),  # Slate-200
        "accent": RGBColor(129, 140, 248),  # Indigo-400
        "footer": RGBColor(100, 116, 139),  # Slate-500
    },
    PresentationTheme.MINIMAL_LIGHT: {
        "bg": RGBColor(248, 250, 252),  # Slate-50
        "card_bg": RGBColor(255, 255, 255),  # Pure White
        "card_border": RGBColor(226, 232, 240),  # Slate-200
        "title": RGBColor(15, 23, 42),  # Slate-900
        "subtitle": RGBColor(71, 85, 105),  # Slate-600
        "text": RGBColor(51, 65, 85),  # Slate-700
        "accent": RGBColor(37, 99, 235),  # Blue-600
        "footer": RGBColor(148, 163, 184),  # Slate-400
    },
    PresentationTheme.ACADEMIC_INDIGO: {
        "bg": RGBColor(30, 27, 75),  # Indigo-950
        "card_bg": RGBColor(49, 46, 129),  # Indigo-900
        "card_border": RGBColor(67, 56, 202),  # Indigo-700
        "title": RGBColor(255, 255, 255),  # White
        "subtitle": RGBColor(199, 210, 254),  # Indigo-200
        "text": RGBColor(224, 231, 255),  # Indigo-100
        "accent": RGBColor(167, 139, 250),  # Violet-400
        "footer": RGBColor(129, 140, 248),  # Indigo-400
    },
    PresentationTheme.CORPORATE_BLUE: {
        "bg": RGBColor(11, 25, 44),  # Corporate Navy
        "card_bg": RGBColor(25, 42, 68),  # Deep Blue Card
        "card_border": RGBColor(39, 64, 102),  # Border
        "title": RGBColor(255, 255, 255),  # White
        "subtitle": RGBColor(186, 230, 253),  # Sky-200
        "text": RGBColor(226, 232, 240),  # Slate-200
        "accent": RGBColor(56, 189, 248),  # Sky-400
        "footer": RGBColor(125, 160, 202),  # Muted Blue
    },
}

ARABIC_REGEX = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


def is_arabic_text(text: str | None) -> bool:
    """Returns True if the text contains Arabic characters."""
    if not text:
        return False
    return bool(ARABIC_REGEX.search(text))


def get_text_alignment(text: str | None) -> Any:
    """Returns PP_ALIGN.RIGHT for Arabic text, otherwise PP_ALIGN.LEFT."""
    return PP_ALIGN.RIGHT if is_arabic_text(text) else PP_ALIGN.LEFT


def detect_slide_layout(slide_number: int, total_slides: int, title: str, content: str) -> str:
    """Detects slide pedagogical layout based on position and content."""
    if slide_number == 1:
        return "title"

    lower_title = (title or "").lower()

    if slide_number == total_slides or any(
        k in lower_title for k in ("conclusion", "questions", "خاتمة", "الخاتمة", "q&a")
    ):
        return "conclusion"

    if slide_number == total_slides - 1 or any(
        k in lower_title
        for k in (
            "synthèse",
            "synthese",
            "résumé",
            "resume",
            "points clés",
            "takeaways",
            "summary",
            "خلاصة",
            "الخلاصة",
        )
    ):
        return "summary"

    if slide_number == 2 or any(
        k in lower_title
        for k in ("sommaire", "agenda", "objectifs", "جدول الأعمال", "محتوى", "مخطط", "roadmap")
    ):
        return "agenda"

    if " || " in (content or ""):
        return "two_column"

    return "concept"


def get_font_scale_for_bullets(line_count: int) -> tuple[Pt, Pt]:
    """Returns (font_size, space_after) scaled dynamically to prevent card overflow."""
    if line_count <= 3:
        return Pt(20), Pt(14)
    elif line_count == 4:
        return Pt(18), Pt(11)
    elif line_count == 5:
        return Pt(16), Pt(8)
    else:
        return Pt(14), Pt(5)


class PPTXExporter:
    """Exports a Presentation and its PresentationSlides into a professional 16:9 PPTX deck.

    Features:
    - 16:9 Widescreen dimensions (13.333 x 7.5 inches).
    - Pedagogical layouts (Title, Agenda, Concept, Two-column, Summary, Conclusion).
    - Arabic RTL automatic detection and right-alignment.
    - Dynamic font scaling to guarantee zero overflow.
    - Speaker notes export into PPTX presentation notes frame.
    - Pre-export validation via PresentationValidator.
    """

    def __init__(self, storage_service: Any = None) -> None:
        self.storage_service = storage_service or get_storage_service()

    def export_to_buffer(self, presentation: Presentation) -> io.BytesIO:
        """Generates PPTX in-memory binary stream."""
        slides = PresentationValidator.validate_deck_for_export(presentation)
        total_slides = len(slides)

        prs = PptxPresentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        palette = THEME_PALETTES.get(
            presentation.theme, THEME_PALETTES[PresentationTheme.MODERN_DARK]
        )
        blank_layout = prs.slide_layouts[6]

        for slide_model in slides:
            slide = prs.slides.add_slide(blank_layout)

            # Set background color
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = palette["bg"]

            layout_type = detect_slide_layout(
                slide_number=slide_model.slide_number,
                total_slides=total_slides,
                title=slide_model.title,
                content=slide_model.content or "",
            )

            if layout_type == "title":
                self._render_title_slide(slide, slide_model, presentation, palette)
            elif layout_type == "agenda":
                self._render_agenda_slide(slide, slide_model, presentation, palette, total_slides)
            elif layout_type == "two_column":
                self._render_two_column_slide(
                    slide, slide_model, presentation, palette, total_slides
                )
            elif layout_type == "summary":
                self._render_summary_slide(slide, slide_model, presentation, palette, total_slides)
            elif layout_type == "conclusion":
                self._render_conclusion_slide(
                    slide, slide_model, presentation, palette, total_slides
                )
            else:
                self._render_content_slide(slide, slide_model, presentation, palette, total_slides)

            # Add speaker notes if provided
            if slide_model.speaker_notes:
                notes_slide = slide.notes_slide
                text_frame = notes_slide.notes_text_frame
                text_frame.text = slide_model.speaker_notes

        buffer = io.BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        return buffer

    def export_and_save(self, presentation: Presentation) -> str:
        """Generates PPTX, stores file via StorageService and updates Presentation."""
        presentation.status = PresentationStatus.EXPORTING
        presentation.save(update_fields=["status", "updated_at"])

        try:
            buffer = self.export_to_buffer(presentation)
            storage_key = f"presentations/{presentation.id}/presentation.pptx"

            self.storage_service.save_file(
                storage_key=storage_key,
                content=buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )

            presentation.storage_key = storage_key
            presentation.status = PresentationStatus.READY
            presentation.save(update_fields=["storage_key", "status", "updated_at"])

            logger.info("Exported PPTX for presentation %s -> %s", presentation.id, storage_key)
            return storage_key

        except Exception as exc:
            presentation.status = PresentationStatus.FAILED
            presentation.save(update_fields=["status", "updated_at"])
            logger.error(
                "Failed exporting PPTX for presentation %s: %s", presentation.id, exc, exc_info=True
            )
            raise

    def _render_title_slide(
        self,
        slide: Any,
        slide_model: PresentationSlide,
        presentation: Presentation,
        palette: dict[str, RGBColor],
    ) -> None:
        """Renders the main hero cover slide."""
        # Hero card container
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(1.2),
            Inches(1.2),
            Inches(10.933),
            Inches(5.1),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = palette["card_bg"]
        card.line.color.rgb = palette["card_border"]
        card.line.width = Pt(1.5)

        is_ar = is_arabic_text(slide_model.title or presentation.title)

        # Organization / Course badge
        badge_box = slide.shapes.add_textbox(Inches(1.8), Inches(1.8), Inches(9.7), Inches(0.5))
        tf_badge = badge_box.text_frame
        p_badge = tf_badge.paragraphs[0]
        org_name = (
            presentation.course.organization.name.upper()
            if presentation.course and presentation.course.organization
            else "AMANUS"
        )
        p_badge.text = f"AMANUS LEARN AI • {org_name}"
        p_badge.font.size = Pt(13)
        p_badge.font.bold = True
        p_badge.font.color.rgb = palette["accent"]
        p_badge.font.name = "Calibri"
        p_badge.alignment = PP_ALIGN.RIGHT if is_ar else PP_ALIGN.LEFT

        # Main Title with auto font size
        title_text = slide_model.title or presentation.title
        title_font_size = Pt(32) if len(title_text) > 40 else Pt(38)

        title_box = slide.shapes.add_textbox(Inches(1.8), Inches(2.4), Inches(9.7), Inches(1.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = title_font_size
        p_title.font.bold = True
        p_title.font.color.rgb = palette["title"]
        p_title.font.name = "Calibri"
        p_title.alignment = PP_ALIGN.RIGHT if is_ar else PP_ALIGN.LEFT

        # Subtitle / Details
        if slide_model.content:
            content_box = slide.shapes.add_textbox(
                Inches(1.8), Inches(4.3), Inches(9.7), Inches(1.6)
            )
            tf_content = content_box.text_frame
            tf_content.word_wrap = True
            lines = [line.strip() for line in slide_model.content.split("\n") if line.strip()]
            for i, line in enumerate(lines):
                p = tf_content.paragraphs[0] if i == 0 else tf_content.add_paragraph()
                p.text = line
                p.font.size = Pt(16)
                p.font.color.rgb = palette["subtitle"]
                p.font.name = "Calibri"
                p.alignment = PP_ALIGN.RIGHT if is_arabic_text(line) else PP_ALIGN.LEFT
                p.space_after = Pt(6)

    def _render_agenda_slide(
        self,
        slide: Any,
        slide_model: PresentationSlide,
        presentation: Presentation,
        palette: dict[str, RGBColor],
        total_slides: int,
    ) -> None:
        """Renders agenda roadmap slide with highlighted milestone list."""
        is_ar = is_arabic_text(slide_model.title)
        badge_text = "جدول الأعمال والأهداف" if is_ar else "SOMMAIRE & OBJECTIFS"

        self._render_header(slide, badge_text, slide_model.title, palette, is_ar)

        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(1.0),
            Inches(2.2),
            Inches(11.333),
            Inches(4.3),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = palette["card_bg"]
        card.line.color.rgb = palette["card_border"]
        card.line.width = Pt(1.2)

        content_box = slide.shapes.add_textbox(Inches(1.4), Inches(2.5), Inches(10.5), Inches(3.7))
        tf = content_box.text_frame
        tf.word_wrap = True

        raw_lines = [
            line.strip() for line in (slide_model.content or "").split("\n") if line.strip()
        ]
        font_size, space_after = get_font_scale_for_bullets(len(raw_lines))

        for i, line in enumerate(raw_lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            clean_text = line.lstrip("•-* ").strip()
            p.text = f"•   {clean_text}"
            p.font.size = font_size
            p.font.bold = False
            p.font.color.rgb = palette["text"]
            p.font.name = "Calibri"
            p.alignment = PP_ALIGN.RIGHT if is_arabic_text(clean_text) else PP_ALIGN.LEFT
            p.space_after = space_after

        self._render_footer(slide, slide_model, presentation, palette, total_slides, is_ar)

    def _render_two_column_slide(
        self,
        slide: Any,
        slide_model: PresentationSlide,
        presentation: Presentation,
        palette: dict[str, RGBColor],
        total_slides: int,
    ) -> None:
        """Renders two-column comparative slide with twin cards."""
        is_ar = is_arabic_text(slide_model.title)
        badge_text = "تحليل ومقارنة" if is_ar else "ANALYSE COMPAREE"

        self._render_header(slide, badge_text, slide_model.title, palette, is_ar)

        parts = (slide_model.content or "").split(" || ")
        left_text = parts[0].strip() if len(parts) > 0 else ""
        right_text = parts[1].strip() if len(parts) > 1 else ""

        # Left Card
        left_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(1.0),
            Inches(2.2),
            Inches(5.45),
            Inches(4.3),
        )
        left_card.fill.solid()
        left_card.fill.fore_color.rgb = palette["card_bg"]
        left_card.line.color.rgb = palette["card_border"]
        left_card.line.width = Pt(1)

        left_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.4), Inches(5.05), Inches(3.9))
        self._populate_column_text(left_box.text_frame, left_text, palette)

        # Right Card
        right_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(6.883),
            Inches(2.2),
            Inches(5.45),
            Inches(4.3),
        )
        right_card.fill.solid()
        right_card.fill.fore_color.rgb = palette["card_bg"]
        right_card.line.color.rgb = palette["card_border"]
        right_card.line.width = Pt(1)

        right_box = slide.shapes.add_textbox(Inches(7.083), Inches(2.4), Inches(5.05), Inches(3.9))
        self._populate_column_text(right_box.text_frame, right_text, palette)

        self._render_footer(slide, slide_model, presentation, palette, total_slides, is_ar)

    def _populate_column_text(self, tf: Any, text: str, palette: dict[str, RGBColor]) -> None:
        """Populates paragraphs in a column text frame with font scaling."""
        tf.word_wrap = True
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        font_size, space_after = get_font_scale_for_bullets(len(lines))

        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            clean_text = line.lstrip("•-* ").strip()
            p.text = f"•  {clean_text}"
            p.font.size = font_size
            p.font.color.rgb = palette["text"]
            p.font.name = "Calibri"
            p.alignment = PP_ALIGN.RIGHT if is_arabic_text(clean_text) else PP_ALIGN.LEFT
            p.space_after = space_after

    def _render_summary_slide(
        self,
        slide: Any,
        slide_model: PresentationSlide,
        presentation: Presentation,
        palette: dict[str, RGBColor],
        total_slides: int,
    ) -> None:
        """Renders summary takeaway slide with highlighted accent border."""
        is_ar = is_arabic_text(slide_model.title)
        badge_text = "الخلاصة والنقاط الجوهرية" if is_ar else "SYNTHESE & POINTS CLES"

        self._render_header(slide, badge_text, slide_model.title, palette, is_ar)

        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(1.0),
            Inches(2.2),
            Inches(11.333),
            Inches(4.3),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = palette["card_bg"]
        card.line.color.rgb = palette["accent"]
        card.line.width = Pt(2)

        content_box = slide.shapes.add_textbox(Inches(1.4), Inches(2.5), Inches(10.5), Inches(3.7))
        tf = content_box.text_frame
        tf.word_wrap = True

        raw_lines = [
            line.strip() for line in (slide_model.content or "").split("\n") if line.strip()
        ]
        font_size, space_after = get_font_scale_for_bullets(len(raw_lines))

        for i, line in enumerate(raw_lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            clean_text = line.lstrip("•-* ").strip()
            p.text = f"✓   {clean_text}"
            p.font.size = font_size
            p.font.bold = False
            p.font.color.rgb = palette["text"]
            p.font.name = "Calibri"
            p.alignment = PP_ALIGN.RIGHT if is_arabic_text(clean_text) else PP_ALIGN.LEFT
            p.space_after = space_after

        self._render_footer(slide, slide_model, presentation, palette, total_slides, is_ar)

    def _render_conclusion_slide(
        self,
        slide: Any,
        slide_model: PresentationSlide,
        presentation: Presentation,
        palette: dict[str, RGBColor],
        total_slides: int,
    ) -> None:
        """Renders conclusion slide with discussion focus."""
        is_ar = is_arabic_text(slide_model.title)
        badge_text = "الخاتمة والأسئلة" if is_ar else "CONCLUSION & ECHANGES"

        self._render_header(slide, badge_text, slide_model.title, palette, is_ar)

        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(1.0),
            Inches(2.2),
            Inches(11.333),
            Inches(4.3),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = palette["card_bg"]
        card.line.color.rgb = palette["card_border"]
        card.line.width = Pt(1.5)

        content_box = slide.shapes.add_textbox(Inches(1.4), Inches(2.6), Inches(10.5), Inches(3.5))
        tf = content_box.text_frame
        tf.word_wrap = True

        raw_lines = [
            line.strip() for line in (slide_model.content or "").split("\n") if line.strip()
        ]
        font_size, space_after = get_font_scale_for_bullets(len(raw_lines))

        for i, line in enumerate(raw_lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            clean_text = line.lstrip("•-* ").strip()
            p.text = f"•   {clean_text}"
            p.font.size = font_size
            p.font.color.rgb = palette["text"]
            p.font.name = "Calibri"
            p.alignment = PP_ALIGN.RIGHT if is_arabic_text(clean_text) else PP_ALIGN.LEFT
            p.space_after = space_after

        self._render_footer(slide, slide_model, presentation, palette, total_slides, is_ar)

    def _render_content_slide(
        self,
        slide: Any,
        slide_model: PresentationSlide,
        presentation: Presentation,
        palette: dict[str, RGBColor],
        total_slides: int,
    ) -> None:
        """Renders standard pedagogical content slide."""
        is_ar = is_arabic_text(slide_model.title)
        badge_text = "محور تعليمي" if is_ar else "MODULE PEDAGOGIQUE"

        self._render_header(slide, badge_text, slide_model.title, palette, is_ar)

        # Main Content Card
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(1.0),
            Inches(2.2),
            Inches(11.333),
            Inches(4.3),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = palette["card_bg"]
        card.line.color.rgb = palette["card_border"]
        card.line.width = Pt(1)

        # Bullets inside Card
        content_box = slide.shapes.add_textbox(Inches(1.4), Inches(2.5), Inches(10.5), Inches(3.7))
        tf = content_box.text_frame
        tf.word_wrap = True

        raw_lines = [
            line.strip() for line in (slide_model.content or "").split("\n") if line.strip()
        ]
        if not raw_lines:
            raw_lines = ["• Présentation des notions clés", "• Analyse pédagogique et illustration"]

        font_size, space_after = get_font_scale_for_bullets(len(raw_lines))

        for i, line in enumerate(raw_lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            clean_text = line.lstrip("•-* ").strip()
            p.text = f"•   {clean_text}"
            p.font.size = font_size
            p.font.color.rgb = palette["text"]
            p.font.name = "Calibri"
            p.alignment = PP_ALIGN.RIGHT if is_arabic_text(clean_text) else PP_ALIGN.LEFT
            p.space_after = space_after

        self._render_footer(slide, slide_model, presentation, palette, total_slides, is_ar)

    def _render_header(
        self,
        slide: Any,
        badge_text: str,
        title_text: str,
        palette: dict[str, RGBColor],
        is_ar: bool,
    ) -> None:
        """Renders top badge and slide title banner."""
        header_box = slide.shapes.add_textbox(
            Inches(1.0), Inches(0.55), Inches(11.333), Inches(0.4)
        )
        tf_hdr = header_box.text_frame
        p_hdr = tf_hdr.paragraphs[0]
        p_hdr.text = badge_text.upper()
        p_hdr.font.size = Pt(12)
        p_hdr.font.bold = True
        p_hdr.font.color.rgb = palette["accent"]
        p_hdr.font.name = "Calibri"
        p_hdr.alignment = PP_ALIGN.RIGHT if is_ar else PP_ALIGN.LEFT

        title_box = slide.shapes.add_textbox(
            Inches(1.0), Inches(0.95), Inches(11.333), Inches(1.15)
        )
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(30) if len(title_text) > 45 else Pt(32)
        p_title.font.bold = True
        p_title.font.color.rgb = palette["title"]
        p_title.font.name = "Calibri"
        p_title.alignment = PP_ALIGN.RIGHT if is_ar else PP_ALIGN.LEFT

    def _render_footer(
        self,
        slide: Any,
        slide_model: PresentationSlide,
        presentation: Presentation,
        palette: dict[str, RGBColor],
        total_slides: int,
        is_ar: bool,
    ) -> None:
        """Renders bottom footer with slide number and course title."""
        footer_box = slide.shapes.add_textbox(
            Inches(1.0), Inches(6.75), Inches(11.333), Inches(0.4)
        )
        tf_ftr = footer_box.text_frame
        p_ftr = tf_ftr.paragraphs[0]
        if is_ar:
            p_ftr.text = (
                f"{presentation.title}  |  الشريحة {slide_model.slide_number} من {total_slides}"
            )
            p_ftr.alignment = PP_ALIGN.RIGHT
        else:
            p_ftr.text = (
                f"{presentation.title}  |  Slide {slide_model.slide_number} sur {total_slides}"
            )
            p_ftr.alignment = PP_ALIGN.LEFT

        p_ftr.font.size = Pt(11)
        p_ftr.font.color.rgb = palette["footer"]
        p_ftr.font.name = "Calibri"
