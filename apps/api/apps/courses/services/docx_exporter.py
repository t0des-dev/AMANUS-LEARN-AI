"""Service exporting Course and its hierarchical sections to a polished Microsoft Word (.docx) document."""

import io

from docx import Document
from docx.shared import Inches, Pt, RGBColor

from apps.courses.models import Course


class CourseDocxExporter:
    """Generates professional, styled DOCX export for a given Course."""

    def __init__(self, course: Course):
        self.course = course

    def generate(self) -> io.BytesIO:
        doc = Document()

        # Set page margins
        sections = doc.sections
        for s in sections:
            s.top_margin = Inches(1.0)
            s.bottom_margin = Inches(1.0)
            s.left_margin = Inches(1.0)
            s.right_margin = Inches(1.0)

        # Title
        title_p = doc.add_paragraph()
        title_p.paragraph_format.space_before = Pt(0)
        title_p.paragraph_format.space_after = Pt(8)
        run_title = title_p.add_run(self.course.title)
        run_title.font.size = Pt(26)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(15, 23, 42)  # slate-900

        # Subtitle / Metadata
        meta_p = doc.add_paragraph()
        meta_p.paragraph_format.space_after = Pt(16)
        meta_run = meta_p.add_run(
            f"Niveau : {self.course.get_level_display()}  |  "
            f"Langue : {self.course.language.upper()}  |  "
            f"Statut : {self.course.get_status_display()}"
        )
        meta_run.font.size = Pt(10)
        meta_run.font.color.rgb = RGBColor(100, 116, 139)  # slate-500

        # Description
        if self.course.description:
            desc_p = doc.add_paragraph()
            desc_p.paragraph_format.space_after = Pt(18)
            desc_run = desc_p.add_run(self.course.description)
            desc_run.font.size = Pt(11)
            desc_run.font.italic = True
            desc_run.font.color.rgb = RGBColor(51, 65, 85)

        doc.add_heading("Table des matières & Structure Pédagogique", level=1)

        # Retrieve chapters (sections where parent is None)
        chapters = (
            self.course.sections.filter(parent__isnull=True)
            .order_by("order", "created_at")
            .prefetch_related("children")
        )

        if not chapters.exists():
            # If flat structure without explicit parent
            flat_sections = self.course.sections.all().order_by("order", "created_at")
            for sec in flat_sections:
                self._render_section(doc, sec, level=2)
        else:
            for chapter in chapters:
                # Chapter Heading
                ch_p = doc.add_heading(level=2)
                ch_p.paragraph_format.space_before = Pt(14)
                ch_p.paragraph_format.space_after = Pt(4)
                ch_run = ch_p.add_run(chapter.title)
                ch_run.font.color.rgb = RGBColor(30, 41, 59)

                if chapter.summary:
                    sum_p = doc.add_paragraph()
                    sum_p.paragraph_format.space_after = Pt(6)
                    sum_run = sum_p.add_run(f"Synthèse : {chapter.summary}")
                    sum_run.font.size = Pt(10)
                    sum_run.font.italic = True
                    sum_run.font.color.rgb = RGBColor(71, 85, 105)

                # Chapter sub-lessons
                children = chapter.children.all().order_by("order", "created_at")
                for child in children:
                    self._render_section(doc, child, level=3)

        # Buffer return
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    def _render_section(self, doc: Document, section, level: int = 2):
        sec_h = doc.add_heading(section.title, level=level)
        sec_h.paragraph_format.space_before = Pt(10)
        sec_h.paragraph_format.space_after = Pt(4)

        if section.estimated_minutes:
            meta_p = doc.add_paragraph()
            meta_p.paragraph_format.space_after = Pt(4)
            dur_run = meta_p.add_run(f"Durée estimée : {section.estimated_minutes} min")
            dur_run.font.size = Pt(9)
            dur_run.font.bold = True
            dur_run.font.color.rgb = RGBColor(99, 102, 241)  # indigo-500

        # Objectives
        if section.objectives and isinstance(section.objectives, list):
            obj_title = doc.add_paragraph()
            obj_title.paragraph_format.space_before = Pt(4)
            obj_title.paragraph_format.space_after = Pt(2)
            obj_title_run = obj_title.add_run("Objectifs d'apprentissage :")
            obj_title_run.font.size = Pt(10)
            obj_title_run.font.bold = True

            for obj in section.objectives:
                p = doc.add_paragraph(style="List Bullet")
                p.paragraph_format.space_after = Pt(2)
                r = p.add_run(str(obj))
                r.font.size = Pt(10)

        # Content
        if section.content:
            lines = section.content.split("\n")
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("### "):
                    h = doc.add_heading(stripped[4:], level=4)
                    h.paragraph_format.space_before = Pt(6)
                    h.paragraph_format.space_after = Pt(2)
                elif stripped.startswith("## "):
                    h = doc.add_heading(stripped[3:], level=3)
                    h.paragraph_format.space_before = Pt(8)
                    h.paragraph_format.space_after = Pt(2)
                elif stripped.startswith("- ") or stripped.startswith("* "):
                    p = doc.add_paragraph(style="List Bullet")
                    p.paragraph_format.space_after = Pt(2)
                    r = p.add_run(stripped[2:])
                    r.font.size = Pt(10.5)
                elif stripped.startswith("> "):
                    p = doc.add_paragraph()
                    p.paragraph_format.left_indent = Inches(0.3)
                    p.paragraph_format.space_after = Pt(4)
                    r = p.add_run(stripped[2:])
                    r.font.italic = True
                    r.font.size = Pt(10)
                    r.font.color.rgb = RGBColor(79, 70, 229)
                else:
                    p = doc.add_paragraph()
                    p.paragraph_format.space_after = Pt(4)
                    r = p.add_run(stripped)
                    r.font.size = Pt(10.5)
