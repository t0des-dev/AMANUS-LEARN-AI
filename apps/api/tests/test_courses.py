import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.courses.models import Course, CourseLevel, CourseSection, CourseStatus
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


# =========================================================================
# Course CRUD & Permissions Tests
# =========================================================================


@pytest.mark.django_db
class TestCourseCRUDAndPermissions:
    def test_teacher_can_create_course(self, api_client, tenant_setup):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]
        api_client.force_authenticate(user=teacher)

        payload = {
            "organization": str(org.id),
            "title": "Introduction au Machine Learning",
            "description": "Cours complet pour débuter.",
            "language": "fr",
            "level": CourseLevel.BEGINNER,
            "status": CourseStatus.DRAFT,
        }

        response = api_client.post("/api/v1/courses/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Introduction au Machine Learning"
        assert str(response.data["created_by"]) == str(teacher.id)

    def test_student_cannot_create_course(self, api_client, tenant_setup):
        student = tenant_setup["student"]
        org = tenant_setup["org_a"]
        api_client.force_authenticate(user=student)

        payload = {
            "organization": str(org.id),
            "title": "Cours non autorisé",
        }
        response = api_client.post("/api/v1/courses/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_courses_scoped_to_organization(self, api_client, tenant_setup):
        teacher = tenant_setup["teacher"]
        outsider = tenant_setup["outsider"]
        org_a = tenant_setup["org_a"]
        org_b = tenant_setup["org_b"]

        Course.objects.create(
            organization=org_a,
            created_by=teacher,
            title="Cours Alpha 1",
        )
        Course.objects.create(
            organization=org_b,
            created_by=outsider,
            title="Cours Beta 1",
        )

        api_client.force_authenticate(user=teacher)
        response = api_client.get("/api/v1/courses/")
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]["title"] == "Cours Alpha 1"

    def test_cross_tenant_cannot_access_or_modify_course(self, api_client, tenant_setup):
        teacher = tenant_setup["teacher"]
        outsider = tenant_setup["outsider"]
        org_a = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org_a,
            created_by=teacher,
            title="Cours Confidentiel Alpha",
        )

        api_client.force_authenticate(user=outsider)
        detail_res = api_client.get(f"/api/v1/courses/{course.id}/")
        assert detail_res.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

        patch_res = api_client.patch(
            f"/api/v1/courses/{course.id}/", {"title": "Piratage"}, format="json"
        )
        assert patch_res.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_teacher_can_update_and_delete_course(self, api_client, tenant_setup):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]
        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Titre Initial",
        )

        api_client.force_authenticate(user=teacher)
        update_res = api_client.patch(
            f"/api/v1/courses/{course.id}/",
            {"title": "Titre Modifié", "level": CourseLevel.ADVANCED},
            format="json",
        )
        assert update_res.status_code == status.HTTP_200_OK
        assert update_res.data["title"] == "Titre Modifié"
        assert update_res.data["level"] == CourseLevel.ADVANCED

        del_res = api_client.delete(f"/api/v1/courses/{course.id}/")
        assert del_res.status_code == status.HTTP_204_NO_CONTENT
        assert not Course.objects.filter(id=course.id).exists()


# =========================================================================
# CourseSection & Hierarchy Tests
# =========================================================================


@pytest.mark.django_db
class TestCourseSectionHierarchy:
    def test_preserve_hierarchy_chapter_section_lesson(self, api_client, tenant_setup):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]
        course = Course.objects.create(
            organization=org, created_by=teacher, title="Sciences Fondamentales"
        )

        api_client.force_authenticate(user=teacher)

        # 1. Create Level 1: Chapter (parent=None)
        res_chap = api_client.post(
            f"/api/v1/courses/{course.id}/sections/",
            {
                "title": "Chapitre 1 : Mécanique Quantique",
                "order": 1,
                "summary": "Introduction à la physique moderne.",
                "estimated_minutes": 60,
            },
            format="json",
        )
        assert res_chap.status_code == status.HTTP_201_CREATED
        chap_id = res_chap.data["id"]

        # 2. Create Level 2: Section (parent=chap_id)
        res_sec = api_client.post(
            f"/api/v1/courses/{course.id}/sections/",
            {
                "parent": chap_id,
                "title": "Section 1.1 : Dualité onde-corpuscule",
                "order": 1,
                "summary": "Concepts fondamentaux.",
                "estimated_minutes": 30,
            },
            format="json",
        )
        assert res_sec.status_code == status.HTTP_201_CREATED
        sec_id = res_sec.data["id"]

        # 3. Create Level 3: Lesson (parent=sec_id)
        res_lesson = api_client.post(
            f"/api/v1/courses/{course.id}/sections/",
            {
                "parent": sec_id,
                "title": "Leçon 1.1.1 : L'expérience des fentes de Young",
                "order": 1,
                "content": "Description détaillée de l'expérience d'interférence.",
                "summary": "Observation du comportement ondulatoire.",
                "objectives": ["Comprendre l'interférence quantique"],
                "estimated_minutes": 15,
            },
            format="json",
        )
        assert res_lesson.status_code == status.HTTP_201_CREATED

        # Verify recursive outline tree from course detail
        detail_res = api_client.get(f"/api/v1/courses/{course.id}/")
        assert detail_res.status_code == status.HTTP_200_OK
        sections_tree = detail_res.data["sections"]
        assert len(sections_tree) == 1
        assert sections_tree[0]["title"] == "Chapitre 1 : Mécanique Quantique"
        assert len(sections_tree[0]["children"]) == 1
        assert sections_tree[0]["children"][0]["title"] == "Section 1.1 : Dualité onde-corpuscule"
        assert len(sections_tree[0]["children"][0]["children"]) == 1
        assert (
            sections_tree[0]["children"][0]["children"][0]["title"]
            == "Leçon 1.1.1 : L'expérience des fentes de Young"
        )

    def test_teacher_can_edit_lesson_content_at_will(self, api_client, tenant_setup):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]
        course = Course.objects.create(organization=org, created_by=teacher, title="Mathématiques")
        lesson = CourseSection.objects.create(
            course=course,
            title="Leçon IA Initiale",
            content="Contenu généré par l'IA.",
            summary="Synthèse initiale.",
        )

        api_client.force_authenticate(user=teacher)

        # Modifying content (never immutable!)
        new_content = "Contenu pédagogique enrichi et corrigé par le professeur."
        response = api_client.patch(
            f"/api/v1/sections/{lesson.id}/",
            {"content": new_content, "title": "Leçon Validée par le Professeur"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        lesson.refresh_from_db()
        assert lesson.content == new_content
        assert lesson.title == "Leçon Validée par le Professeur"

    def test_cannot_assign_parent_from_another_course(self, api_client, tenant_setup):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]
        course_1 = Course.objects.create(organization=org, created_by=teacher, title="Cours 1")
        course_2 = Course.objects.create(organization=org, created_by=teacher, title="Cours 2")

        chap_course_1 = CourseSection.objects.create(course=course_1, title="Chapitre Cours 1")

        api_client.force_authenticate(user=teacher)
        # Attempt to create section in course 2 with parent from course 1
        response = api_client.post(
            f"/api/v1/courses/{course_2.id}/sections/",
            {
                "parent": str(chap_course_1.id),
                "title": "Section Invalide",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "parent" in response.data


# =========================================================================
# AI Course Generation Tests
# =========================================================================


@pytest.mark.django_db
class TestAICourseGeneration:
    def test_generate_course_from_analyzed_document(
        self, api_client, tenant_setup, analyzed_document
    ):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Nouveau cours",
            document=analyzed_document,
        )

        api_client.force_authenticate(user=teacher)

        url = f"/api/v1/courses/{course.id}/generate/"
        response = api_client.post(url, {"provider": "mock", "top_k": 5}, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        # Check title was populated
        assert data["title"] is not None
        assert len(data["sections"]) > 0

        # Verify hierarchical materialized sections in database
        course.refresh_from_db()
        assert course.sections.count() >= 3

        # Check Chapters (parent=None)
        chapters = course.sections.filter(parent__isnull=True)
        assert chapters.count() >= 2

        # Check Lessons with content and objectives
        lessons = course.sections.filter(parent__isnull=False)
        assert lessons.exists()
        lesson = lessons.filter(content__gt="").first()
        assert lesson is not None
        assert len(lesson.objectives) > 0
        assert lesson.estimated_minutes > 0

    def test_student_cannot_trigger_course_generation(
        self, api_client, tenant_setup, analyzed_document
    ):
        student = tenant_setup["student"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            title="Cours Verrouillé",
            document=analyzed_document,
        )

        api_client.force_authenticate(user=student)
        url = f"/api/v1/courses/{course.id}/generate/"
        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
