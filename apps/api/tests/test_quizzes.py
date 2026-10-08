import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.ai.services import InsufficientContextError
from apps.courses.models import Course
from apps.documents.models import Document, DocumentStatus
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.organizations.models import Organization, OrganizationMember, RoleChoices
from apps.quizzes.models import (
    DifficultyLevel,
    Quiz,
    QuizAnswer,
    QuizQuestion,
    QuizType,
)
from apps.quizzes.services import (
    InvalidQuizQuestionError,
    QuizAttemptService,
    QuizGeneratorService,
    QuizQuestionValidator,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant_fixture(db):
    user_owner = User.objects.create_user(
        email="owner@org.com",
        password="Password123!",
        first_name="Owner",
        last_name="Org",
    )
    user_teacher = User.objects.create_user(
        email="teacher@org.com",
        password="Password123!",
        first_name="Teacher",
        last_name="Org",
    )
    user_student = User.objects.create_user(
        email="student@org.com",
        password="Password123!",
        first_name="Student",
        last_name="Org",
    )
    user_outsider = User.objects.create_user(
        email="outsider@other.com",
        password="Password123!",
        first_name="Outsider",
        last_name="Other",
    )

    org_a = Organization.objects.create(name="Org A", slug="org-a")
    OrganizationMember.objects.create(organization=org_a, user=user_owner, role=RoleChoices.OWNER)
    OrganizationMember.objects.create(
        organization=org_a, user=user_teacher, role=RoleChoices.TEACHER
    )
    OrganizationMember.objects.create(
        organization=org_a, user=user_student, role=RoleChoices.STUDENT
    )

    org_b = Organization.objects.create(name="Org B", slug="org-b")
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
def sample_quiz(db, tenant_fixture):
    org = tenant_fixture["org_a"]
    teacher = tenant_fixture["teacher"]

    quiz = Quiz.objects.create(
        organization=org,
        created_by=teacher,
        title="QCM Intelligence Artificielle",
        description="Quiz d'évaluation sur les réseaux de neurones",
        type=QuizType.TRAINING,
        difficulty=DifficultyLevel.MEDIUM,
        time_limit_minutes=20,
        passing_score_percentage=75,
    )

    # Question 1
    q1 = QuizQuestion.objects.create(
        quiz=quiz,
        text="Quelle est la fonction d'activation souvent utilisée en sortie d'une classification binaire ?",
        explanation="La fonction Sigmoïde produit une sortie entre 0 et 1 assimilable à une probabilité.",
        difficulty=DifficultyLevel.EASY,
        source="Chapitre 1 : Fonctions d'activation",
        order=0,
    )
    a1_1 = QuizAnswer.objects.create(question=q1, text="Sigmoïde", is_correct=True, order=0)
    a1_2 = QuizAnswer.objects.create(question=q1, text="ReLU", is_correct=False, order=1)
    QuizAnswer.objects.create(question=q1, text="Softmax", is_correct=False, order=2)
    QuizAnswer.objects.create(question=q1, text="Tanh", is_correct=False, order=3)

    # Question 2
    q2 = QuizQuestion.objects.create(
        quiz=quiz,
        text="Quel est l'effet de l'abandon (dropout) durant l'entraînement ?",
        explanation="Le dropout désactive aléatoirement des neurones pour prévenir le surapprentissage.",
        difficulty=DifficultyLevel.MEDIUM,
        source="Chapitre 2 : Régularisation",
        order=1,
    )
    a2_1 = QuizAnswer.objects.create(
        question=q2,
        text="Prévenir le surapprentissage (overfitting)",
        is_correct=True,
        order=0,
    )
    a2_2 = QuizAnswer.objects.create(
        question=q2,
        text="Accélérer le calcul des gradients",
        is_correct=False,
        order=1,
    )
    QuizAnswer.objects.create(
        question=q2,
        text="Augmenter le nombre de paramètres",
        is_correct=False,
        order=2,
    )
    QuizAnswer.objects.create(
        question=q2,
        text="Réduire la taille du jeu de données",
        is_correct=False,
        order=3,
    )

    return {
        "quiz": quiz,
        "q1": q1,
        "q2": q2,
        "a1_correct": a1_1,
        "a1_wrong": a1_2,
        "a2_correct": a2_1,
        "a2_wrong": a2_2,
    }


@pytest.fixture
def document_with_content(db, tenant_fixture):
    org = tenant_fixture["org_a"]
    teacher = tenant_fixture["teacher"]

    doc = Document.objects.create(
        organization=org,
        owner=teacher,
        title="Cours d'Apprentissage Profond",
        file_name="dl.pdf",
        file_type="pdf",
        file_size=1024,
        storage_key="test/dl.pdf",
        status=DocumentStatus.READY,
    )

    page = DocumentPage.objects.create(
        document=doc,
        page_number=1,
        text="L'apprentissage profond repose sur des réseaux de neurones multicouches.",
    )

    DocumentChunk.objects.create(
        document=doc,
        page=page,
        chunk_index=0,
        content="Le mécanisme d'attention pondère l'importance des tokens dans les Transformers.",
        token_count=20,
        metadata={"chapter": "Attention", "section": "1.1"},
        embedding=[0.05] * 128,
    )

    return doc


# =========================================================================
# Unit Tests: Validation JSON & Détection des Questions Invalides
# =========================================================================


class TestQuizQuestionValidation:
    def test_valid_question_passes(self):
        validator = QuizQuestionValidator()
        raw = {
            "question": "Quel est le mécanisme clé des Transformers ?",
            "answers": [
                {"text": "Attention multi-têtes", "is_correct": True},
                {"text": "Pooling max", "is_correct": False},
                {"text": "Convolution 1D", "is_correct": False},
                {"text": "Régression ridge", "is_correct": False},
            ],
            "explanation": "L'attention permet de pondérer les tokens.",
            "difficulty": "MEDIUM",
            "source": "Chapitre 1",
        }
        validated = validator.validate_and_normalize(raw)
        assert validated["text"] == "Quel est le mécanisme clé des Transformers ?"
        assert len(validated["answers"]) == 4
        assert sum(1 for a in validated["answers"] if a["is_correct"] is True) == 1

    def test_reject_if_not_4_answers(self):
        validator = QuizQuestionValidator()
        raw_3_options = {
            "question": "Question avec 3 réponses ?",
            "answers": [
                {"text": "A", "is_correct": True},
                {"text": "B", "is_correct": False},
                {"text": "C", "is_correct": False},
            ],
            "explanation": "Explication",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_info:
            validator.validate_and_normalize(raw_3_options)
        assert "exactement 4 options" in str(exc_info.value)

    def test_reject_if_multiple_correct_or_zero_correct(self):
        validator = QuizQuestionValidator()
        raw_zero_correct = {
            "question": "Question sans bonne réponse ?",
            "answers": [
                {"text": "A", "is_correct": False},
                {"text": "B", "is_correct": False},
                {"text": "C", "is_correct": False},
                {"text": "D", "is_correct": False},
            ],
            "explanation": "Explication",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_0:
            validator.validate_and_normalize(raw_zero_correct)
        assert "UNE seule bonne réponse" in str(exc_0.value)

        raw_two_correct = {
            "question": "Question avec 2 bonnes réponses ?",
            "answers": [
                {"text": "A", "is_correct": True},
                {"text": "B", "is_correct": True},
                {"text": "C", "is_correct": False},
                {"text": "D", "is_correct": False},
            ],
            "explanation": "Explication",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_2:
            validator.validate_and_normalize(raw_two_correct)
        assert "UNE seule bonne réponse" in str(exc_2.value)

    def test_reject_duplicate_options(self):
        validator = QuizQuestionValidator()
        raw_duplicate = {
            "question": "Question avec doublon ?",
            "answers": [
                {"text": "Option A", "is_correct": True},
                {"text": "Option A", "is_correct": False},
                {"text": "Option B", "is_correct": False},
                {"text": "Option C", "is_correct": False},
            ],
            "explanation": "Explication",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_dup:
            validator.validate_and_normalize(raw_duplicate)
        assert "doublon" in str(exc_dup.value)

    def test_reject_empty_question_or_explanation(self):
        validator = QuizQuestionValidator()
        raw_empty_q = {
            "question": "   ",
            "answers": [
                {"text": "A", "is_correct": True},
                {"text": "B", "is_correct": False},
                {"text": "C", "is_correct": False},
                {"text": "D", "is_correct": False},
            ],
            "explanation": "Explication",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc:
            validator.validate_and_normalize(raw_empty_q)
        assert "manquant ou vide" in str(exc.value)


# =========================================================================
# Unit Tests: Scoring & Attempt Evaluation
# =========================================================================


@pytest.mark.django_db
class TestQuizScoringAndAttempts:
    def test_perfect_score_evaluation(self, sample_quiz, tenant_fixture):
        quiz = sample_quiz["quiz"]
        student = tenant_fixture["student"]
        service = QuizAttemptService()

        attempt = service.start_attempt(quiz, student)
        assert attempt.started_at is not None
        assert attempt.completed_at is None

        answers_payload = {
            str(sample_quiz["q1"].id): str(sample_quiz["a1_correct"].id),
            str(sample_quiz["q2"].id): str(sample_quiz["a2_correct"].id),
        }

        eval_res = service.submit_attempt(attempt, answers_payload)
        assert eval_res["score"] == 100.0
        assert eval_res["correct_answers_count"] == 2
        assert eval_res["total_questions"] == 2
        assert eval_res["passed"] is True
        assert attempt.passed is True
        assert attempt.completed_at is not None

    def test_partial_score_evaluation_and_pass_fail(self, sample_quiz, tenant_fixture):
        quiz = sample_quiz["quiz"]
        student = tenant_fixture["student"]
        service = QuizAttemptService()

        attempt = service.start_attempt(quiz, student)
        # Answer Q1 correctly, Q2 wrongly
        answers_payload = {
            str(sample_quiz["q1"].id): str(sample_quiz["a1_correct"].id),
            str(sample_quiz["q2"].id): str(sample_quiz["a2_wrong"].id),
        }

        eval_res = service.submit_attempt(attempt, answers_payload)
        assert eval_res["score"] == 50.0
        assert eval_res["correct_answers_count"] == 1
        # Passing score is 75%, so 50% fails
        assert eval_res["passed"] is False
        assert attempt.passed is False

        # Verify reviews returned
        reviews = eval_res["questions_review"]
        assert len(reviews) == 2
        assert reviews[0]["is_correct"] is True
        assert reviews[1]["is_correct"] is False
        assert reviews[1]["explanation"] != ""


# =========================================================================
# Integration Tests: AI Generation Engine with Validation
# =========================================================================


@pytest.mark.django_db
class TestAIQuizGeneration:
    def test_generate_questions_with_mock_provider(self, sample_quiz, document_with_content):
        quiz = sample_quiz["quiz"]
        gen_service = QuizGeneratorService()

        created = gen_service.generate_questions_for_quiz(
            quiz=quiz,
            document=document_with_content,
            provider_name="mock",
            count=2,
        )

        assert len(created) >= 2
        for q in created:
            assert q.answers.count() == 4
            assert q.answers.filter(is_correct=True).count() == 1
            assert q.explanation != ""
            assert q.source != ""

    def test_refuse_if_document_has_no_chunks(self, sample_quiz, tenant_fixture):
        quiz = sample_quiz["quiz"]
        empty_doc = Document.objects.create(
            organization=tenant_fixture["org_a"],
            owner=tenant_fixture["teacher"],
            title="Doc Vide",
            file_name="empty.pdf",
            file_type="pdf",
            file_size=100,
            storage_key="test/empty.pdf",
            status=DocumentStatus.UPLOADED,
        )

        gen_service = QuizGeneratorService()
        with pytest.raises(InsufficientContextError) as exc_info:
            gen_service.generate_questions_for_quiz(quiz=quiz, document=empty_doc)
        assert "ne contient aucun chunk" in str(exc_info.value)


# =========================================================================
# Integration Tests: API Endpoints & Permissions
# =========================================================================


@pytest.mark.django_db
class TestQuizAPIEndpoints:
    def test_teacher_can_create_quiz(self, api_client, tenant_fixture):
        teacher = tenant_fixture["teacher"]
        org = tenant_fixture["org_a"]
        api_client.force_authenticate(user=teacher)

        payload = {
            "organization": str(org.id),
            "title": "Quiz sur la Vision par Ordinateur",
            "type": "EXAM",
            "difficulty": "HARD",
            "time_limit_minutes": 30,
            "passing_score_percentage": 80,
        }
        res = api_client.post("/api/v1/quizzes/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["title"] == "Quiz sur la Vision par Ordinateur"
        assert res.data["type"] == "EXAM"

    def test_student_cannot_create_quiz(self, api_client, tenant_fixture):
        student = tenant_fixture["student"]
        org = tenant_fixture["org_a"]
        api_client.force_authenticate(user=student)

        payload = {
            "organization": str(org.id),
            "title": "Quiz non autorisé",
        }
        res = api_client.post("/api/v1/quizzes/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_student_cannot_see_is_correct_flag_in_detail_view(
        self, api_client, sample_quiz, tenant_fixture
    ):
        student = tenant_fixture["student"]
        quiz = sample_quiz["quiz"]
        api_client.force_authenticate(user=student)

        res = api_client.get(f"/api/v1/quizzes/{quiz.id}/")
        assert res.status_code == status.HTTP_200_OK

        questions = res.data["questions"]
        assert len(questions) > 0
        first_answer = questions[0]["answers"][0]
        # Student should NOT see is_correct attribute before submitting
        assert "is_correct" not in first_answer

    def test_start_and_submit_attempt_endpoints(self, api_client, sample_quiz, tenant_fixture):
        student = tenant_fixture["student"]
        quiz = sample_quiz["quiz"]
        api_client.force_authenticate(user=student)

        # 1. Start attempt
        start_res = api_client.post(f"/api/v1/quizzes/{quiz.id}/start/")
        assert start_res.status_code == status.HTTP_201_CREATED
        attempt_id = start_res.data["id"]

        # 2. Submit attempt
        submit_payload = {
            "attempt_id": attempt_id,
            "answers": {
                str(sample_quiz["q1"].id): str(sample_quiz["a1_correct"].id),
                str(sample_quiz["q2"].id): str(sample_quiz["a2_correct"].id),
            },
        }
        submit_res = api_client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/", submit_payload, format="json"
        )
        assert submit_res.status_code == status.HTTP_200_OK
        assert submit_res.data["score"] == 100.0
        assert submit_res.data["passed"] is True

        # 3. Retrieve results history
        results_res = api_client.get(f"/api/v1/quizzes/{quiz.id}/results/")
        assert results_res.status_code == status.HTTP_200_OK
        assert results_res.data["total_attempts"] == 1
        assert results_res.data["best_score"] == 100.0

    def test_cross_tenant_cannot_access_or_play_quiz(self, api_client, sample_quiz, tenant_fixture):
        outsider = tenant_fixture["outsider"]
        quiz = sample_quiz["quiz"]
        api_client.force_authenticate(user=outsider)

        res_detail = api_client.get(f"/api/v1/quizzes/{quiz.id}/")
        assert res_detail.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

        res_start = api_client.post(f"/api/v1/quizzes/{quiz.id}/start/")
        assert res_start.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_course_quizzes_list_and_create(
        self, api_client, tenant_fixture, document_with_content
    ):
        teacher = tenant_fixture["teacher"]
        org = tenant_fixture["org_a"]
        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Cours pour Quiz",
            document=document_with_content,
        )

        api_client.force_authenticate(user=teacher)

        # Create quiz linked to course
        create_res = api_client.post(
            f"/api/v1/courses/{course.id}/quizzes/",
            {
                "title": "Quiz de fin de cours",
                "type": "EXAM",
                "difficulty": "MEDIUM",
                "generate_ai": True,
                "questions_count": 2,
            },
            format="json",
        )
        assert create_res.status_code == status.HTTP_201_CREATED
        assert str(create_res.data["course"]) == str(course.id)

        # List quizzes for course
        list_res = api_client.get(f"/api/v1/courses/{course.id}/quizzes/")
        assert list_res.status_code == status.HTTP_200_OK
        assert len(list_res.data) >= 1
