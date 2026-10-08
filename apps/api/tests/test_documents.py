import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.documents.models import Document, DocumentStatus
from apps.documents.services.storage import reset_storage_service
from apps.organizations.models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


class DocumentManagerAPITests(APITestCase):
    """Comprehensive test suite for Document Management, multi-tenant isolation,

    upload validation, permissions, processing and purge.
    """

    def setUp(self):
        # Create temp dir for media storage tests
        self.temp_media_dir = tempfile.mkdtemp()
        self.media_override = override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            CELERY_TASK_ALWAYS_EAGER=True,
            STORAGE_BACKEND="local",
        )
        self.media_override.enable()
        reset_storage_service()

        # Tenant A: Alice (Owner) and Charles (Student)
        self.user_a = User.objects.create_user(
            email="alice@tenant-a.com",
            password="PasswordA123!",
            first_name="Alice",
            last_name="Alpha",
        )
        self.org_a = Organization.objects.create(name="Organization Alpha")
        self.member_a = OrganizationMember.objects.create(
            organization=self.org_a,
            user=self.user_a,
            role=RoleChoices.OWNER,
        )

        self.student_a = User.objects.create_user(
            email="student@tenant-a.com",
            password="PasswordS123!",
            first_name="Charlie",
            last_name="Student",
        )
        self.member_student_a = OrganizationMember.objects.create(
            organization=self.org_a,
            user=self.student_a,
            role=RoleChoices.STUDENT,
        )

        # Tenant B: Bob (Owner)
        self.user_b = User.objects.create_user(
            email="bob@tenant-b.com",
            password="PasswordB123!",
            first_name="Bob",
            last_name="Beta",
        )
        self.org_b = Organization.objects.create(name="Organization Beta")
        self.member_b = OrganizationMember.objects.create(
            organization=self.org_b,
            user=self.user_b,
            role=RoleChoices.OWNER,
        )

        # URLs
        self.doc_list_create_url = reverse("v1:documents:document-list-create")

    def tearDown(self):
        self.media_override.disable()
        reset_storage_service()
        shutil.rmtree(self.temp_media_dir, ignore_errors=True)

    def authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    # =========================================================================
    # Upload & Format Validation Tests
    # =========================================================================

    def test_upload_pdf_document_success(self):
        """A tenant member with OWNER/ADMIN role can upload a valid PDF document."""
        self.authenticate_as(self.user_a)
        pdf_file = SimpleUploadedFile(
            "cours_intro.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )

        payload = {
            "file": pdf_file,
            "organization_id": str(self.org_a.id),
            "title": "Introduction à l'IA",
            "description": "Cours complet d'initiation",
            "language": "fr",
        }

        response = self.client.post(self.doc_list_create_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Introduction à l'IA")
        self.assertEqual(response.data["file_type"], "pdf")
        self.assertEqual(response.data["status"], DocumentStatus.UPLOADED)
        self.assertIn("download_url", response.data)

        # Verify DB entry
        doc = Document.objects.get(id=response.data["id"])
        self.assertEqual(doc.organization, self.org_a)
        self.assertEqual(doc.owner, self.user_a)

    def test_upload_supported_formats_docx_pptx_txt(self):
        """Accepts valid DOCX, PPTX and TXT files."""
        self.authenticate_as(self.user_a)

        formats = [
            (
                "document.docx",
                b"PK\x03\x04\x14\x00\x00\x00docx_payload",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "docx",
            ),
            (
                "presentation.pptx",
                b"PK\x03\x04\x14\x00\x00\x00pptx_payload",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "pptx",
            ),
            (
                "synthese.txt",
                b"Ceci est un texte clair et informatif.",
                "text/plain",
                "txt",
            ),
        ]

        for filename, content, mime, expected_type in formats:
            upload_file = SimpleUploadedFile(filename, content, content_type=mime)
            res = self.client.post(
                self.doc_list_create_url,
                {
                    "file": upload_file,
                    "organization_id": str(self.org_a.id),
                },
                format="multipart",
            )
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertEqual(res.data["file_type"], expected_type)

    def test_upload_invalid_extension_rejected(self):
        """Unsupported file extensions like .exe or .zip are rejected with 400."""
        self.authenticate_as(self.user_a)
        bad_file = SimpleUploadedFile(
            "malware.exe", b"MZ\x90\x00binary", content_type="application/x-msdownload"
        )

        res = self.client.post(
            self.doc_list_create_url,
            {"file": bad_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res.data)

    def test_upload_fake_pdf_magic_signature_rejected(self):
        """Files pretending to be PDF without %PDF header are rejected."""
        self.authenticate_as(self.user_a)
        fake_pdf = SimpleUploadedFile(
            "fake.pdf", b"NOT_A_PDF_HEADER", content_type="application/pdf"
        )

        res = self.client.post(
            self.doc_list_create_url,
            {"file": fake_pdf, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res.data)

    def test_upload_file_size_exceeded_rejected(self):
        """Uploading files exceeding MAX_DOCUMENT_SIZE returns 400."""
        self.authenticate_as(self.user_a)
        small_limit = 100  # 100 bytes

        with override_settings(MAX_DOCUMENT_SIZE=small_limit):
            large_content = b"%PDF-1.4\n" + b"A" * 200
            oversized_pdf = SimpleUploadedFile(
                "big.pdf", large_content, content_type="application/pdf"
            )

            res = self.client.post(
                self.doc_list_create_url,
                {"file": oversized_pdf, "organization_id": str(self.org_a.id)},
                format="multipart",
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # Explicit Multi-Tenant Isolation Tests (Critical Rule)
    # =========================================================================

    def test_explicit_multi_tenant_isolation_cross_tenant_read_forbidden(self):
        """User A in Org A cannot read documents belonging to Org B, and vice versa."""
        # Create doc in Org A by Alice
        doc_a = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Secret Org A Strategy",
            file_name="secret_a.pdf",
            file_type="pdf",
            file_size=1024,
            storage_key=f"organizations/{self.org_a.id}/documents/secret_a.pdf",
        )

        # Authenticate as Bob (Org B)
        self.authenticate_as(self.user_b)

        # 1. Direct GET by UUID on Org A document returns 404 (not found / isolated)
        detail_url = reverse("v1:documents:document-detail", kwargs={"id": doc_a.id})
        res_detail = self.client.get(detail_url)
        self.assertEqual(res_detail.status_code, status.HTTP_404_NOT_FOUND)

        # 2. General list endpoint for Bob returns ONLY documents of Org B
        res_list = self.client.get(self.doc_list_create_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        results = res_list.data.get("results", res_list.data)
        doc_ids = [d["id"] for d in results]
        self.assertNotIn(str(doc_a.id), doc_ids)

        # 3. Explicitly querying ?organization_id=OrgA by Bob returns 403 Forbidden
        res_query_org_a = self.client.get(
            f"{self.doc_list_create_url}?organization_id={self.org_a.id}"
        )
        self.assertEqual(res_query_org_a.status_code, status.HTTP_403_FORBIDDEN)

    def test_explicit_multi_tenant_isolation_cross_tenant_update_forbidden(self):
        """User B in Org B cannot modify a document belonging to Org A."""
        doc_a = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Org A Roadmap",
            file_name="roadmap.pdf",
            file_type="pdf",
            file_size=2048,
            storage_key=f"organizations/{self.org_a.id}/documents/roadmap.pdf",
        )

        self.authenticate_as(self.user_b)
        detail_url = reverse("v1:documents:document-detail", kwargs={"id": doc_a.id})

        res_patch = self.client.patch(detail_url, {"title": "Hacked Title"}, format="json")
        self.assertEqual(res_patch.status_code, status.HTTP_404_NOT_FOUND)

        doc_a.refresh_from_db()
        self.assertEqual(doc_a.title, "Org A Roadmap")

    def test_explicit_multi_tenant_isolation_cross_tenant_delete_forbidden(self):
        """User B in Org B cannot delete a document belonging to Org A."""
        doc_a = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Org A Critical Document",
            file_name="critical.pdf",
            file_type="pdf",
            file_size=4096,
            storage_key=f"organizations/{self.org_a.id}/documents/critical.pdf",
        )

        self.authenticate_as(self.user_b)
        detail_url = reverse("v1:documents:document-detail", kwargs={"id": doc_a.id})

        res_del = self.client.delete(detail_url)
        self.assertEqual(res_del.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Document.objects.filter(id=doc_a.id).exists())

    def test_non_member_cannot_upload_to_organization(self):
        """User B cannot upload documents into Organization A."""
        self.authenticate_as(self.user_b)
        pdf_file = SimpleUploadedFile(
            "attack.pdf",
            b"%PDF-1.4\ncontent",
            content_type="application/pdf",
        )

        res = self.client.post(
            self.doc_list_create_url,
            {"file": pdf_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # Delete & Storage Purge Tests
    # =========================================================================

    def test_document_delete_purges_file_from_storage(self):
        """Authorized deletion removes DB record and purges physical file from storage."""
        self.authenticate_as(self.user_a)
        pdf_file = SimpleUploadedFile(
            "to_delete.pdf",
            b"%PDF-1.4\nremovable_bytes",
            content_type="application/pdf",
        )

        res_upload = self.client.post(
            self.doc_list_create_url,
            {"file": pdf_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        self.assertEqual(res_upload.status_code, status.HTTP_201_CREATED)
        doc_id = res_upload.data["id"]
        doc = Document.objects.get(id=doc_id)

        # Verify file exists in temp storage
        storage_path = Path(self.temp_media_dir) / doc.storage_key
        self.assertTrue(storage_path.is_file())

        # Perform deletion
        detail_url = reverse("v1:documents:document-detail", kwargs={"id": doc.id})
        res_del = self.client.delete(detail_url)
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)

        # Assert removed from DB and disk
        self.assertFalse(Document.objects.filter(id=doc_id).exists())
        self.assertFalse(storage_path.is_file())

    # =========================================================================
    # Process & Status Pipeline Tests
    # =========================================================================

    def test_document_process_pipeline_staging(self):
        """POST /documents/{id}/process stages the pipeline and updates status."""
        self.authenticate_as(self.user_a)

        # Upload a TXT file
        txt_file = SimpleUploadedFile(
            "cours.txt",
            b"Introduction aux architectures Transformers et LLMs. " * 50,
            content_type="text/plain",
        )
        res_upload = self.client.post(
            self.doc_list_create_url,
            {"file": txt_file, "organization_id": str(self.org_a.id)},
            format="multipart",
        )
        doc_id = res_upload.data["id"]

        # Call process endpoint
        process_url = reverse("v1:documents:document-process", kwargs={"id": doc_id})
        res_process = self.client.post(process_url)
        self.assertEqual(res_process.status_code, status.HTTP_200_OK)
        self.assertEqual(res_process.data["id"], str(doc_id))
        self.assertIn("message", res_process.data)

        # Check document status endpoint
        status_url = reverse("v1:documents:document-status", kwargs={"id": doc_id})
        res_status = self.client.get(status_url)
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        self.assertIn(res_status.data["status"], [DocumentStatus.PROCESSING, DocumentStatus.READY])
        self.assertGreaterEqual(res_status.data["page_count"], 1)

    def test_cross_tenant_cannot_trigger_process_or_check_status(self):
        """User B cannot trigger process or view status for Org A document."""
        doc_a = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Org A Doc",
            file_name="doc.txt",
            file_type="txt",
            file_size=500,
            storage_key=f"organizations/{self.org_a.id}/documents/doc.txt",
        )

        self.authenticate_as(self.user_b)
        process_url = reverse("v1:documents:document-process", kwargs={"id": doc_a.id})
        status_url = reverse("v1:documents:document-status", kwargs={"id": doc_a.id})

        res_p = self.client.post(process_url)
        self.assertEqual(res_p.status_code, status.HTTP_404_NOT_FOUND)

        res_s = self.client.get(status_url)
        self.assertEqual(res_s.status_code, status.HTTP_404_NOT_FOUND)
