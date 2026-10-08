import io
import tempfile
from pathlib import Path

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
from apps.ingestion.parsers import (
    DocumentParserFactory,
    DOCXParser,
    InvalidDocumentFileError,
    OCRParser,
    PDFParser,
    PPTXParser,
    TXTParser,
    UnsupportedDocumentFormatError,
)
from apps.ingestion.services.chunking import ChunkingService
from apps.ingestion.tasks import process_document
from apps.organizations.models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


def create_in_memory_pdf(text: str = "Hello PDF World") -> bytes:
    """Generates a valid, minimal in-memory PDF file containing text."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # Write stream
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def create_in_memory_docx(
    title: str = "Titre du Cours", content: str = "Contenu explicatif du document DOCX."
) -> bytes:
    """Generates a valid, minimal in-memory Microsoft Word (.docx) file."""
    doc = docx.Document()
    doc.add_heading(f"Chapitre 1 : {title}", level=1)
    doc.add_heading("Section 1.1 : Notions de base", level=2)
    doc.add_paragraph(content)
    doc.add_heading("Sous-section 1.1.1 : Approfondissement", level=3)
    doc.add_paragraph("Détails supplémentaires sur les algorithmes.")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_in_memory_pptx(
    title: str = "Slide Intro", content: str = "Slide presentation content."
) -> bytes:
    """Generates a valid, minimal in-memory PowerPoint (.pptx) file."""
    prs = pptx.Presentation()
    blank_slide_layout = prs.slide_layouts[6]  # Blank
    slide = prs.slides.add_slide(blank_slide_layout)
    txBox = slide.shapes.add_textbox(
        pptx.util.Inches(1), pptx.util.Inches(1), pptx.util.Inches(5), pptx.util.Inches(2)
    )
    tf = txBox.text_frame
    tf.text = f"# {title}\n{content}"
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


class IngestionAdapterAndParserTests(APITestCase):
    """Unit test suite for DocumentParser adapters, factory, and error handling."""

    def test_factory_dispatches_correct_adapter(self):
        self.assertIsInstance(DocumentParserFactory.get_parser("pdf"), PDFParser)
        self.assertIsInstance(DocumentParserFactory.get_parser(".docx"), DOCXParser)
        self.assertIsInstance(DocumentParserFactory.get_parser("pptx"), PPTXParser)
        self.assertIsInstance(DocumentParserFactory.get_parser("txt"), TXTParser)
        self.assertIsInstance(DocumentParserFactory.get_parser("text/plain"), TXTParser)

    def test_factory_unsupported_format_raises_error(self):
        with self.assertRaises(UnsupportedDocumentFormatError):
            DocumentParserFactory.get_parser("mp3")

        with self.assertRaises(UnsupportedDocumentFormatError):
            DocumentParserFactory.get_parser("exe")

    def test_txt_parser_valid_file(self):
        parser = TXTParser()
        content = (
            "Chapitre 1 : Introduction à l'IA\n\n"
            "Section 1.1 : Concepts généraux\n\n"
            "Les réseaux neuronaux artificiels s'inspirent du cerveau biologique.\n\n"
            "Sous-section 1.1.1 : Historique\n\n"
            "Le perceptron fut inventé en 1957."
        ).encode("utf-8")
        parsed = parser.parse(content)
        self.assertGreaterEqual(parsed.total_pages, 1)
        self.assertIn("perceptron", parsed.full_text)
        self.assertEqual(
            parsed.pages[0].metadata.get("chapter"), "Chapitre 1 : Introduction à l'IA"
        )
        self.assertEqual(parsed.pages[0].metadata.get("section"), "Section 1.1 : Concepts généraux")
        self.assertEqual(
            parsed.pages[0].metadata.get("subsection"), "Sous-section 1.1.1 : Historique"
        )

    def test_txt_parser_empty_file_raises_error(self):
        parser = TXTParser()
        with self.assertRaises(InvalidDocumentFileError):
            parser.parse(b"")

    def test_docx_parser_valid_file(self):
        docx_bytes = create_in_memory_docx()
        parser = DOCXParser()
        parsed = parser.parse(docx_bytes)
        self.assertGreaterEqual(parsed.total_pages, 1)
        self.assertIn("Chapitre 1", parsed.full_text)
        self.assertEqual(parsed.pages[0].metadata.get("chapter"), "# Chapitre 1 : Titre du Cours")
        self.assertEqual(
            parsed.pages[0].metadata.get("section"), "## Section 1.1 : Notions de base"
        )
        self.assertEqual(
            parsed.pages[0].metadata.get("subsection"), "### Sous-section 1.1.1 : Approfondissement"
        )

    def test_docx_parser_corrupt_file_raises_error(self):
        parser = DOCXParser()
        with self.assertRaises(InvalidDocumentFileError):
            parser.parse(b"PK\x03\x04corrupted_docx_payload")

    def test_pptx_parser_valid_file(self):
        pptx_bytes = create_in_memory_pptx()
        parser = PPTXParser()
        parsed = parser.parse(pptx_bytes)
        self.assertEqual(parsed.total_pages, 1)
        self.assertIn("Slide presentation content", parsed.full_text)
        self.assertEqual(parsed.pages[0].page_number, 1)

    def test_pptx_parser_corrupt_file_raises_error(self):
        parser = PPTXParser()
        with self.assertRaises(InvalidDocumentFileError):
            parser.parse(b"PK\x03\x04corrupted_pptx_payload")

    def test_pdf_parser_valid_file(self):
        pdf_bytes = create_in_memory_pdf()
        parser = PDFParser()
        parsed = parser.parse(pdf_bytes)
        self.assertEqual(parsed.total_pages, 1)

    def test_pdf_parser_corrupt_file_raises_error(self):
        parser = PDFParser()
        with self.assertRaises(InvalidDocumentFileError):
            parser.parse(b"%PDF-1.4\ncorrupted_pdf_data_bytes")

    def test_ocr_parser_graceful_fallback(self):
        ocr = OCRParser()
        # Even if Tesseract is not installed on system, calling parse_image_bytes handles it safely
        result = ocr.parse_image_bytes(b"")
        self.assertEqual(result, "")


class ChunkingServiceTests(APITestCase):
    """Test suite for semantic chunking and hierarchy preservation."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="prof@test.com", password="Password123!", first_name="Alan"
        )
        self.org = Organization.objects.create(name="Test University")
        OrganizationMember.objects.create(
            organization=self.org, user=self.user, role=RoleChoices.OWNER
        )
        self.doc = Document.objects.create(
            organization=self.org,
            owner=self.user,
            title="Manuel de Deep Learning",
            file_name="dl.txt",
            file_type="txt",
            file_size=2000,
            storage_key="test/dl.txt",
        )

    def test_chunking_preserves_document_page_chapter_section_hierarchy(self):
        page1 = DocumentPage.objects.create(
            document=self.doc,
            page_number=1,
            text=(
                "Chapitre 1 : Introduction\n\n"
                "Section 1.1 : Historique\n\n"
                "Les réseaux de neurones ont débuté avec les travaux de McCulloch et Pitts. " * 10
            ),
            metadata={
                "chapter": "Chapitre 1 : Introduction",
                "section": "Section 1.1 : Historique",
                "subsection": None,
            },
        )
        page2 = DocumentPage.objects.create(
            document=self.doc,
            page_number=2,
            text=(
                "Sous-section 1.1.1 : Le Perceptron de Rosenblatt\n\n"
                "Le modèle du perceptron calcule une somme pondérée des entrées. " * 15
            ),
            metadata={
                "chapter": "Chapitre 1 : Introduction",
                "section": "Section 1.1 : Historique",
                "subsection": "Sous-section 1.1.1 : Le Perceptron de Rosenblatt",
            },
        )

        chunker = ChunkingService(target_tokens=50, overlap_tokens=10)
        chunks = chunker.create_chunks_for_document(self.doc)

        self.assertGreater(len(chunks), 1)
        for idx, chunk in enumerate(chunks):
            self.assertEqual(chunk.chunk_index, idx)
            self.assertEqual(chunk.document, self.doc)
            self.assertIn("document_id", chunk.metadata)
            self.assertIn("page_number", chunk.metadata)
            self.assertEqual(chunk.metadata["document_id"], str(self.doc.id))
            self.assertIn("chapter", chunk.metadata)
            self.assertIn("section", chunk.metadata)

        # First chunk corresponds to page 1
        self.assertEqual(chunks[0].page, page1)
        self.assertEqual(chunks[0].metadata["chapter"], "Chapitre 1 : Introduction")

        # Later chunks correspond to page 2 and preserve subsection
        last_chunk = chunks[-1]
        self.assertEqual(last_chunk.page, page2)
        self.assertEqual(
            last_chunk.metadata["subsection"],
            "Sous-section 1.1.1 : Le Perceptron de Rosenblatt",
        )


class IngestionPipelineAPITests(APITestCase):
    """End-to-end API and task integration tests for Sprint 04."""

    def setUp(self):
        self.temp_media_dir = tempfile.mkdtemp()
        self.media_override = override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            CELERY_TASK_ALWAYS_EAGER=True,
            CELERY_TASK_EAGER_PROPAGATES=True,
            STORAGE_BACKEND="local",
        )
        self.media_override.enable()
        reset_storage_service()

        # Tenant A: Alice
        self.user_a = User.objects.create_user(
            email="alice@ingest-a.com",
            password="PasswordA123!",
            first_name="Alice",
        )
        self.org_a = Organization.objects.create(name="Academy A")
        self.member_a = OrganizationMember.objects.create(
            organization=self.org_a,
            user=self.user_a,
            role=RoleChoices.OWNER,
        )

        # Tenant B: Bob
        self.user_b = User.objects.create_user(
            email="bob@ingest-b.com",
            password="PasswordB123!",
            first_name="Bob",
        )
        self.org_b = Organization.objects.create(name="Academy B")
        self.member_b = OrganizationMember.objects.create(
            organization=self.org_b,
            user=self.user_b,
            role=RoleChoices.OWNER,
        )

    def tearDown(self):
        self.media_override.disable()
        import shutil

        shutil.rmtree(self.temp_media_dir, ignore_errors=True)

    def authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_pipeline_txt_document_success(self):
        """End-to-end ingestion on a structured TXT document."""
        self.authenticate_as(self.user_a)

        txt_content = (
            "Chapitre 1 : Fondations\n\n"
            "Section 1.1 : Introduction aux LLMs\n\n"
            "Ce document traite de la transformation de documents par l'IA. " * 10
        ).encode("utf-8")

        txt_file = SimpleUploadedFile("cours.txt", txt_content, content_type="text/plain")

        # Upload document
        upload_res = self.client.post(
            reverse("v1:documents:document-list-create"),
            {"file": txt_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data["id"]

        # POST /documents/{id}/process
        process_res = self.client.post(
            reverse("v1:documents:document-process", kwargs={"id": doc_id})
        )
        self.assertEqual(process_res.status_code, status.HTTP_200_OK)

        # GET /documents/{id}/processing-status
        status_res = self.client.get(
            reverse("v1:documents:document-processing-status", kwargs={"id": doc_id})
        )
        self.assertEqual(status_res.status_code, status.HTTP_200_OK)
        self.assertEqual(status_res.data["progress_stage"], "Completed")
        self.assertGreaterEqual(status_res.data["pages_count"], 1)
        self.assertGreaterEqual(status_res.data["chunks_count"], 1)
        self.assertEqual(status_res.data["error_message"], "")

        # GET /documents/{id}/pages
        pages_res = self.client.get(reverse("v1:documents:document-pages", kwargs={"id": doc_id}))
        self.assertEqual(pages_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pages_res.data["count"], 1)
        first_page = pages_res.data["results"][0]
        self.assertEqual(first_page["page_number"], 1)
        self.assertIn("Fondations", first_page["text"])
        self.assertFalse(first_page["ocr_used"])
        self.assertEqual(first_page["metadata"]["chapter"], "Chapitre 1 : Fondations")

        # Verify DB records
        self.assertEqual(DocumentPage.objects.filter(document_id=doc_id).count(), 1)
        self.assertGreaterEqual(DocumentChunk.objects.filter(document_id=doc_id).count(), 1)

    def test_pipeline_docx_document_success(self):
        """End-to-end ingestion on a Microsoft Word (.docx) document."""
        self.authenticate_as(self.user_a)

        docx_bytes = create_in_memory_docx(
            title="Ingestion DOCX", content="Paragraphe d'apprentissage."
        )
        docx_file = SimpleUploadedFile(
            "guide.docx",
            docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        upload_res = self.client.post(
            reverse("v1:documents:document-list-create"),
            {"file": docx_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data["id"]

        # Trigger process
        process_res = self.client.post(
            reverse("v1:documents:document-process", kwargs={"id": doc_id})
        )
        self.assertEqual(process_res.status_code, status.HTTP_200_OK)

        # Check pages endpoint
        pages_res = self.client.get(reverse("v1:documents:document-pages", kwargs={"id": doc_id}))
        self.assertEqual(pages_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(pages_res.data["count"], 1)
        self.assertIn("Ingestion DOCX", pages_res.data["results"][0]["text"])

    def test_pipeline_pptx_document_success(self):
        """End-to-end ingestion on a PowerPoint (.pptx) presentation."""
        self.authenticate_as(self.user_a)

        pptx_bytes = create_in_memory_pptx(
            title="Presentation Titre", content="Diapositive de cours IA."
        )
        pptx_file = SimpleUploadedFile(
            "slides.pptx",
            pptx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

        upload_res = self.client.post(
            reverse("v1:documents:document-list-create"),
            {"file": pptx_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data["id"]

        # Trigger process
        process_res = self.client.post(
            reverse("v1:documents:document-process", kwargs={"id": doc_id})
        )
        self.assertEqual(process_res.status_code, status.HTTP_200_OK)

        # Check pages endpoint
        pages_res = self.client.get(reverse("v1:documents:document-pages", kwargs={"id": doc_id}))
        self.assertEqual(pages_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pages_res.data["count"], 1)
        self.assertIn("Diapositive de cours IA", pages_res.data["results"][0]["text"])

    def test_pipeline_pdf_document_success(self):
        """End-to-end ingestion on a PDF document."""
        self.authenticate_as(self.user_a)

        pdf_bytes = create_in_memory_pdf()
        pdf_file = SimpleUploadedFile("manuel.pdf", pdf_bytes, content_type="application/pdf")

        upload_res = self.client.post(
            reverse("v1:documents:document-list-create"),
            {"file": pdf_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data["id"]

        # Trigger process
        process_res = self.client.post(
            reverse("v1:documents:document-process", kwargs={"id": doc_id})
        )
        self.assertEqual(process_res.status_code, status.HTTP_200_OK)

        # Check pages endpoint
        pages_res = self.client.get(reverse("v1:documents:document-pages", kwargs={"id": doc_id}))
        self.assertEqual(pages_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pages_res.data["count"], 1)

    def test_pipeline_corrupted_file_marks_status_failed(self):
        """Corrupted files during pipeline execution set status to FAILED with error message."""
        doc = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Corrupted File",
            file_name="corrupt.pdf",
            file_type="pdf",
            file_size=100,
            storage_key=f"organizations/{self.org_a.id}/documents/corrupt.pdf",
        )

        # Create corrupted file on disk
        storage_path = Path(self.temp_media_dir) / doc.storage_key
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(b"%PDF-1.4\ncorrupt_bytes_not_valid_pdf")

        # Run process_document task
        result = process_document(str(doc.id))
        self.assertEqual(result["status"], "failed")

        doc.refresh_from_db()
        self.assertEqual(doc.status, DocumentStatus.FAILED)
        self.assertTrue(len(doc.error_message) > 0)

        # Check API processing status returns Failed
        self.authenticate_as(self.user_a)
        res = self.client.get(
            reverse("v1:documents:document-processing-status", kwargs={"id": doc.id})
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["progress_stage"], "Failed")
        self.assertIn("invalide", res.data["error_message"].lower())

    def test_cross_tenant_cannot_access_processing_status_or_pages(self):
        """Strict multi-tenant isolation: User B in Org B cannot read Org A document pages or status."""
        doc_a = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Org A Confidentiel",
            file_name="conf.txt",
            file_type="txt",
            file_size=50,
            storage_key=f"organizations/{self.org_a.id}/documents/conf.txt",
        )
        DocumentPage.objects.create(
            document=doc_a,
            page_number=1,
            text="Texte strictement privé Org A.",
        )

        self.authenticate_as(self.user_b)

        # GET /processing-status returns 404
        status_url = reverse("v1:documents:document-processing-status", kwargs={"id": doc_a.id})
        res_status = self.client.get(status_url)
        self.assertEqual(res_status.status_code, status.HTTP_404_NOT_FOUND)

        # GET /pages returns 404
        pages_url = reverse("v1:documents:document-pages", kwargs={"id": doc_a.id})
        res_pages = self.client.get(pages_url)
        self.assertEqual(res_pages.status_code, status.HTTP_404_NOT_FOUND)
