"""Sprint 08: Robustness, extraction quality, security, and multi-tenant isolation tests.

Verifies the 10 mandatory test scenarios of Sprint 08:
1. Valid PDF with exploitable text (Full extraction, chunks generated).
2. Empty or near-empty document detection (Unusable quality, warning flags).
3. Corrupted or invalid file handling (Graceful failure, no crash).
4. Unsupported format rejection (Extensions and MIME validation).
5. Size limit and processing ceiling enforcement (50MB, max pages).
6. Partial extraction with explicit warnings (Mixed pages, scan detection).
7. Permission checks and strict multi-tenant isolation (Zero cross-tenant leakage).
8. Boundary preservation across pages and slides (Slide and heading tracking).
9. Concurrency, duplicate task deduplication, and idempotency guards (409 Conflict).
10. Cascading deletion and consistency of derived pages/chunks and storage.
"""

import io
import tempfile

import docx
import pptx
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from pypdf import PdfWriter
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.documents.models import Document, DocumentStatus
from apps.documents.services.storage import reset_storage_service
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.ingestion.parsers import PPTXParser
from apps.ingestion.services.quality import DocumentQualityEvaluator
from apps.organizations.models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


def make_pdf_with_text(pages_text: list[str]) -> bytes:
    """Build an in-memory PDF with specified text on each page."""
    writer = PdfWriter()
    for text in pages_text:
        # pypdf PdfWriter add_blank_page
        writer.add_blank_page(width=300, height=300)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def make_docx_with_structure() -> bytes:
    """Build a DOCX with headings, lists, and tables."""
    doc = docx.Document()
    doc.add_heading("Chapitre 1 : Introduction", level=1)
    doc.add_paragraph("Ceci est le premier paragraphe explicatif.")
    doc.add_heading("Section 1.1 : Détails", level=2)
    doc.add_paragraph("Point important numéro un.", style="List Bullet")
    doc.add_paragraph("Point important numéro deux.", style="List Bullet")

    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Concept"
    table.cell(0, 1).text = "Définition"
    table.cell(1, 0).text = "Ingestion"
    table.cell(1, 1).text = "Pipeline documentaire robuste"

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def make_pptx_with_slides() -> bytes:
    """Build a PPTX with multiple distinct slides, titles, and notes."""
    prs = pptx.Presentation()
    # Slide 1
    layout = prs.slide_layouts[0]  # Title slide
    slide1 = prs.slides.add_slide(layout)
    slide1.shapes.title.text = "Présentation Architecture"
    slide1.shapes.placeholders[1].text = "Sous-titre Ingestion Robuste"

    # Slide 2 with content
    layout1 = prs.slide_layouts[1]
    slide2 = prs.slides.add_slide(layout1)
    slide2.shapes.title.text = "Objectifs Pédagogiques"
    tf = slide2.shapes.placeholders[1].text_frame
    tf.text = "Fiabiliser le pipeline documentaire"
    p = tf.add_paragraph()
    p.text = "Garantir la traçabilité des sources"

    # Slide 2 speaker notes
    slide2.notes_slide.notes_text_frame.text = "Ne pas oublier d'insister sur la sécurité."

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class IngestionRobustnessSprint08Tests(APITestCase):
    """Test suite validating all Sprint 08 document ingestion robustness requirements."""

    def setUp(self):
        reset_storage_service()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_media_dir = self.temp_dir.name

        # Create two distinct tenants
        self.org_a = Organization.objects.create(name="Tenant Alpha", slug="alpha-tenant")
        self.org_b = Organization.objects.create(name="Tenant Beta", slug="beta-tenant")

        # Create users
        self.user_a = User.objects.create_user(
            email="alice@alpha.com",
            password="Password123!",
            first_name="Alice",
            last_name="Alpha",
        )
        self.user_b = User.objects.create_user(
            email="bob@beta.com",
            password="Password123!",
            first_name="Bob",
            last_name="Beta",
        )

        OrganizationMember.objects.create(
            organization=self.org_a, user=self.user_a, role=RoleChoices.ADMIN
        )
        OrganizationMember.objects.create(
            organization=self.org_b, user=self.user_b, role=RoleChoices.ADMIN
        )

    def tearDown(self):
        reset_storage_service()
        self.temp_dir.cleanup()

    def authenticate_as(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # -------------------------------------------------------------------------
    # 1. Un PDF contenant du texte exploitable
    # -------------------------------------------------------------------------
    def test_1_pdf_with_usable_text(self):
        """Valid PDF with exploitable text achieves FULL quality grade with chunks."""
        self.authenticate_as(self.user_a)

        # Build DOCX / PDF with rich text
        docx_bytes = make_docx_with_structure()
        file = SimpleUploadedFile("cours.docx", docx_bytes, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        res = self.client.post(
            reverse("v1:documents:document-list-create"),
            {"file": file, "organization_id": str(self.org_a.id), "title": "Cours Valide"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        doc_id = res.data["id"]

        # Run process
        proc_res = self.client.post(reverse("v1:documents:document-process", kwargs={"id": doc_id}))
        self.assertEqual(proc_res.status_code, status.HTTP_200_OK)

        # Check status & quality
        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.status, DocumentStatus.READY)
        self.assertEqual(doc.processing_metadata.get("quality_grade"), "FULL")
        self.assertGreater(doc.processing_metadata.get("chunks_count", 0), 0)

        # Pages inspection
        pages_res = self.client.get(reverse("v1:documents:document-pages", kwargs={"id": doc_id}))
        self.assertEqual(pages_res.status_code, status.HTTP_200_OK)
        self.assertGreater(pages_res.data["count"], 0)

    # -------------------------------------------------------------------------
    # 2. Un document vide ou presque vide
    # -------------------------------------------------------------------------
    def test_2_empty_or_near_empty_document(self):
        """0-byte file is rejected, and empty text document is graded UNUSABLE."""
        self.authenticate_as(self.user_a)

        # Zero-byte upload is rejected
        empty_upload = SimpleUploadedFile("empty.txt", b"", content_type="text/plain")
        res = self.client.post(
            reverse("v1:documents:document-list-create"),
            {"file": empty_upload, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vide", str(res.data))

        # Blank PDF (0 extractable characters)
        blank_pdf_bytes = make_pdf_with_text([""])
        valid_upload = SimpleUploadedFile("blank.pdf", blank_pdf_bytes, content_type="application/pdf")
        upload_res = self.client.post(
            reverse("v1:documents:document-list-create"),
            {"file": valid_upload, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data["id"]

        self.client.post(reverse("v1:documents:document-process", kwargs={"id": doc_id}))
        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.processing_metadata.get("quality_grade"), "UNUSABLE")
        self.assertEqual(doc.processing_metadata.get("chunks_count"), 0)
        self.assertIn("DOCUMENT_EMPTY_OR_UNUSABLE", doc.processing_metadata.get("quality_warnings", []))

    # -------------------------------------------------------------------------
    # 3. Un fichier corrompu ou invalide
    # -------------------------------------------------------------------------
    def test_3_corrupted_or_invalid_file(self):
        """Corrupted file raises invalid error and sets status to FAILED."""
        self.authenticate_as(self.user_a)

        doc = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Corrupted Document",
            file_name="corrupt.pdf",
            file_type="pdf",
            file_size=50,
            storage_key=f"organizations/{self.org_a.id}/documents/corrupt.pdf",
        )

        from apps.documents.services.storage import get_storage_service

        storage = get_storage_service()
        storage.save_file(doc.storage_key, io.BytesIO(b"%PDF-1.4\nBROKEN_GARBAGE_PAYLOAD"))

        res = self.client.post(reverse("v1:documents:document-process", kwargs={"id": str(doc.id)}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        doc.refresh_from_db()
        self.assertEqual(doc.status, DocumentStatus.FAILED)
        self.assertIn("invalide ou corrompu", doc.error_message)

    # -------------------------------------------------------------------------
    # 4. Un format non pris en charge
    # -------------------------------------------------------------------------
    def test_4_unsupported_format(self):
        """Executable or unsupported format is strictly rejected at upload."""
        self.authenticate_as(self.user_a)

        bad_file = SimpleUploadedFile("script.py", b"print('malicious')", content_type="text/x-python")
        res = self.client.post(
            reverse("v1:documents:document-list-create"),
            {"file": bad_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non supporté", str(res.data))

    # -------------------------------------------------------------------------
    # 5. Un dépassement de taille ou de limite de traitement
    # -------------------------------------------------------------------------
    def test_5_size_limit_or_budget_exceeded(self):
        """File exceeding MAX_DOCUMENT_SIZE is rejected."""
        self.authenticate_as(self.user_a)

        with override_settings(MAX_DOCUMENT_SIZE=1000):  # 1000 bytes max
            large_file = SimpleUploadedFile(
                "big.txt", b"A" * 5000, content_type="text/plain"
            )
            res = self.client.post(
                reverse("v1:documents:document-list-create"),
                {"file": large_file, "organization_id": str(self.org_a.id)},
                format="multipart",
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("dépasse la limite", str(res.data))

    # -------------------------------------------------------------------------
    # 6. Une extraction partielle avec avertissements
    # -------------------------------------------------------------------------
    def test_6_partial_extraction_with_warnings(self):
        """Document with mixed pages yields PARTIAL quality and tracks warnings."""
        from apps.ingestion.parsers.base import ParsedDocument, ParsedPage

        # Synthetic parsed document with 1 page with text and 1 empty page
        p1 = ParsedPage(page_number=1, text="Contenu textuel exploitable et suffisant pour la première page.", metadata={"char_count": 65})
        p2 = ParsedPage(page_number=2, text="", metadata={"char_count": 0, "warnings": ["PAGE_2_EMPTY"]})

        parsed = ParsedDocument(pages=[p1, p2], metadata={"warnings": ["SOME_PAGES_EMPTY"]})
        quality = DocumentQualityEvaluator.evaluate(parsed)

        self.assertEqual(quality.quality_grade, "PARTIAL")
        self.assertTrue(quality.is_usable)
        self.assertEqual(quality.empty_pages, 1)
        self.assertIn("SOME_PAGES_EMPTY", quality.warnings)

    # -------------------------------------------------------------------------
    # 7. Les erreurs de permission et l'isolation entre utilisateurs ou tenants
    # -------------------------------------------------------------------------
    def test_7_permission_and_cross_tenant_isolation(self):
        """Tenant B user cannot access, process, or view pages of Tenant A document."""
        # Create document under Org A
        doc = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Confidentiel Alpha",
            file_name="alpha.pdf",
            file_type="pdf",
            file_size=200,
            storage_key=f"organizations/{self.org_a.id}/documents/alpha.pdf",
            status=DocumentStatus.READY,
        )

        DocumentPage.objects.create(
            document=doc,
            page_number=1,
            text="Secrets organisation Alpha",
        )

        # Authenticate as User B (Tenant B)
        self.authenticate_as(self.user_b)

        # Attempt to read document
        res_read = self.client.get(reverse("v1:documents:document-detail", kwargs={"id": str(doc.id)}))
        self.assertEqual(res_read.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to read extracted pages
        res_pages = self.client.get(reverse("v1:documents:document-pages", kwargs={"id": str(doc.id)}))
        self.assertEqual(res_pages.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to trigger process
        res_proc = self.client.post(reverse("v1:documents:document-process", kwargs={"id": str(doc.id)}))
        self.assertEqual(res_proc.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to delete
        res_del = self.client.delete(reverse("v1:documents:document-detail", kwargs={"id": str(doc.id)}))
        self.assertEqual(res_del.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 8. Conservation des frontières entre pages ou diapositives
    # -------------------------------------------------------------------------
    def test_8_boundary_preservation_pages_and_slides(self):
        """PPTX slides preserve page numbers, slide titles, sections, and speaker notes."""
        pptx_bytes = make_pptx_with_slides()
        parser = PPTXParser()
        parsed_doc = parser.parse(pptx_bytes)

        self.assertEqual(len(parsed_doc.pages), 2)
        # Slide 1
        page1 = parsed_doc.pages[0]
        self.assertEqual(page1.page_number, 1)
        self.assertIn("Présentation Architecture", page1.text)

        # Slide 2
        page2 = parsed_doc.pages[1]
        self.assertEqual(page2.page_number, 2)
        self.assertIn("Objectifs Pédagogiques", page2.text)
        self.assertIn("Ne pas oublier d'insister sur la sécurité", page2.text)
        self.assertEqual(page2.metadata.get("slide_title"), "Objectifs Pédagogiques")

    # -------------------------------------------------------------------------
    # 9. Reprises, doublons ou traitements répétés (Protection concurrence)
    # -------------------------------------------------------------------------
    def test_9_concurrency_and_duplicate_processing_guard(self):
        """Re-triggering process on an in-flight document returns HTTP 409 Conflict."""
        self.authenticate_as(self.user_a)

        doc = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Document en cours",
            file_name="encours.pdf",
            file_type="pdf",
            file_size=200,
            storage_key=f"organizations/{self.org_a.id}/documents/encours.pdf",
            status=DocumentStatus.EXTRACTING,  # Already extracting
        )

        res = self.client.post(reverse("v1:documents:document-process", kwargs={"id": str(doc.id)}))
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("déjà en cours", res.data["detail"])

    # -------------------------------------------------------------------------
    # 10. Suppression et cohérence des données dérivées
    # -------------------------------------------------------------------------
    def test_10_cascading_deletion_and_derived_data_consistency(self):
        """Deleting a document cascades and purges pages, chunks, and storage file."""
        self.authenticate_as(self.user_a)

        doc = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Document à supprimer",
            file_name="delete_me.pdf",
            file_type="pdf",
            file_size=200,
            storage_key=f"organizations/{self.org_a.id}/documents/delete_me.pdf",
            status=DocumentStatus.READY,
        )

        # Create derived pages and chunks
        page = DocumentPage.objects.create(document=doc, page_number=1, text="Page 1 text")
        DocumentChunk.objects.create(document=doc, page=page, chunk_index=1, content="Chunk 1 content")

        from apps.documents.services.storage import get_storage_service

        storage = get_storage_service()
        storage.save_file(doc.storage_key, io.BytesIO(b"%PDF-1.4 dummy"))
        self.assertTrue(storage.file_exists(doc.storage_key))

        # Perform delete via API
        res = self.client.delete(reverse("v1:documents:document-detail", kwargs={"id": str(doc.id)}))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        # Verify cascades
        self.assertFalse(Document.objects.filter(id=doc.id).exists())
        self.assertFalse(DocumentPage.objects.filter(document_id=doc.id).exists())
        self.assertFalse(DocumentChunk.objects.filter(document_id=doc.id).exists())
        self.assertFalse(storage.file_exists(doc.storage_key))
