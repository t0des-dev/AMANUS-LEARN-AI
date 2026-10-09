import io
import logging
from typing import Any

from pptx import Presentation as PptxPresentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from apps.documents.services.storage import get_storage_service
from apps.slides.models import (
    Presentation,
    PresentationSlide,
    PresentationStatus,
    PresentationTheme,
)

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


class PPTXExporter:
    """Exports a Presentation and its PresentationSlides into a professional 16:9 PPTX deck."""

    def __init__(self, storage_service: Any = None) -> None:
        self.storage_service = storage_service or get_storage_service()

    def export_to_buffer(self, presentation: Presentation) -> io.BytesIO:
        """Generates PPTX in-memory binary stream."""
        prs = PptxPresentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        palette = THEME_PALETTES.get(presentation.theme, THEME_PALETTES[PresentationTheme.MODERN_DARK])
        slides = list(presentation.slides.all().order_by("slide_number", "created_at"))
        total_slides = len(slides)

        blank_layout = prs.slide_layouts[6]

        for idx, slide_model in enumerate(slides):
            slide = prs.slides.add_slide(blank_layout)

            # Set background color
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = palette["bg"]

            is_first_slide = idx == 0

            if is_first_slide:
                self._render_title_slide(slide, slide_model, presentation, palette)
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
            logger.error("Failed exporting PPTX for presentation %s: %s", presentation.id, exc, exc_info=True)
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

        # Organization / Course badge
        badge_box = slide.shapes.add_textbox(Inches(1.8), Inches(1.8), Inches(9.7), Inches(0.5))
        tf_badge = badge_box.text_frame
        p_badge = tf_badge.paragraphs[0]
        p_badge.text = f"AMANUS LEARN AI • {presentation.course.organization.name.upper()}"
        p_badge.font.size = Pt(14)
        p_badge.font.bold = True
        p_badge.font.color.rgb = palette["accent"]

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(1.8), Inches(2.4), Inches(9.7), Inches(1.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = slide_model.title or presentation.title
        p_title.font.size = Pt(40)
        p_title.font.bold = True
        p_title.font.color.rgb = palette["title"]

        # Subtitle / Details
        if slide_model.content:
            content_box = slide.shapes.add_textbox(Inches(1.8), Inches(4.3), Inches(9.7), Inches(1.6))
            tf_content = content_box.text_frame
            tf_content.word_wrap = True
            lines = [line.strip() for line in slide_model.content.split("\n") if line.strip()]
            for i, line in enumerate(lines):
                p = tf_content.paragraphs[0] if i == 0 else tf_content.add_paragraph()
                p.text = line
                p.font.size = Pt(18)
                p.font.color.rgb = palette["subtitle"]
                p.space_after = Pt(8)

    def _render_content_slide(
        self,
        slide: Any,
        slide_model: PresentationSlide,
        presentation: Presentation,
        palette: dict[str, RGBColor],
        total_slides: int,
    ) -> None:
        """Renders standard pedagogical content slides."""
        # Top banner with category/badge
        header_box = slide.shapes.add_textbox(Inches(1.0), Inches(0.6), Inches(11.333), Inches(0.4))
        tf_hdr = header_box.text_frame
        p_hdr = tf_hdr.paragraphs[0]
        p_hdr.text = f"{presentation.title.upper()} — MODULE PEDAGOGIQUE"
        p_hdr.font.size = Pt(12)
        p_hdr.font.bold = True
        p_hdr.font.color.rgb = palette["accent"]

        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.333), Inches(1.1))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = slide_model.title
        p_title.font.size = Pt(32)
        p_title.font.bold = True
        p_title.font.color.rgb = palette["title"]

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
        tf_content = content_box.text_frame
        tf_content.word_wrap = True

        raw_lines = [line.strip() for line in (slide_model.content or "").split("\n") if line.strip()]
        if not raw_lines:
            raw_lines = ["• Présentation des notions clés", "• Analyse pédagogique et illustration"]

        for i, line in enumerate(raw_lines):
            p = tf_content.paragraphs[0] if i == 0 else tf_content.add_paragraph()
            clean_text = line.lstrip("•-* ").strip()
            p.text = f"•   {clean_text}"
            p.font.size = Pt(20)
            p.font.color.rgb = palette["text"]
            p.space_after = Pt(16)

        # Bottom Footer (Slide number & info)
        footer_box = slide.shapes.add_textbox(Inches(1.0), Inches(6.75), Inches(11.333), Inches(0.4))
        tf_ftr = footer_box.text_frame
        p_ftr = tf_ftr.paragraphs[0]
        p_ftr.text = f"{presentation.title}  |  Slide {slide_model.slide_number} sur {total_slides}"
        p_ftr.font.size = Pt(11)
        p_ftr.font.color.rgb = palette["footer"]
