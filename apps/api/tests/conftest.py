import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document, DocumentStatus
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.organizations.models import Organization, OrganizationMember, RoleChoices


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant_setup(db):
    user_owner = User.objects.create_user(
        email="owner@alpha.com",
        password="Password123!",
        first_name="Owner",
        last_name="Alpha",
    )
    user_teacher = User.objects.create_user(
        email="teacher@alpha.com",
        password="Password123!",
        first_name="Teacher",
        last_name="Alpha",
    )
    user_student = User.objects.create_user(
        email="student@alpha.com",
        password="Password123!",
        first_name="Student",
        last_name="Alpha",
    )
    user_outsider = User.objects.create_user(
        email="outsider@beta.com",
        password="Password123!",
        first_name="Outsider",
        last_name="Beta",
    )

    org_a = Organization.objects.create(name="Alpha University", slug="alpha-univ")
    OrganizationMember.objects.create(organization=org_a, user=user_owner, role=RoleChoices.OWNER)
    OrganizationMember.objects.create(
        organization=org_a, user=user_teacher, role=RoleChoices.TEACHER
    )
    OrganizationMember.objects.create(
        organization=org_a, user=user_student, role=RoleChoices.STUDENT
    )

    org_b = Organization.objects.create(name="Beta Academy", slug="beta-acad")
    OrganizationMember.objects.create(
        organization=org_b, user=user_outsider, role=RoleChoices.OWNER
    )

    return {
        "org_a": org_a,
        "org_b": org_b,
        "owner": user_owner,
        "teacher": user_teacher,
        "student": user_student,
        "outsider": user_outsider,
    }


@pytest.fixture
def analyzed_document(db, tenant_setup):
    org = tenant_setup["org_a"]
    teacher = tenant_setup["teacher"]

    doc = Document.objects.create(
        organization=org,
        owner=teacher,
        title="Principes des Réseaux Neuronaux",
        file_name="neural_networks.pdf",
        file_type="pdf",
        file_size=2048,
        storage_key="test/neural_networks.pdf",
        status=DocumentStatus.READY,
    )

    page = DocumentPage.objects.create(
        document=doc,
        page_number=1,
        text="Introduction approfondie à l'architecture des Transformers.",
    )

    DocumentChunk.objects.create(
        document=doc,
        page=page,
        chunk_index=0,
        content=(
            "Les modèles Transformers reposent sur le mécanisme d'auto-attention multi-têtes. "
            "Contrairement aux réseaux récurrents, ils permettent une parallélisation complète."
        ),
        token_count=35,
        metadata={"chapter": "Chapitre 1", "section": "Auto-attention"},
        embedding=[0.05] * 128,
    )

    return doc
