import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document, DocumentStatus
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.organizations.models import Organization, OrganizationMember, RoleChoices
from apps.quizzes.models import DifficultyLevel, Quiz, QuizAnswer, QuizQuestion, QuizType
from apps.quizzes.services import (
    AttemptAlreadyCompletedError,
    InvalidQuizQuestionError,
    QuizAttemptService,
    QuizGeneratorService,
    QuizQuestionValidator,
    parse_boolean_value,
    sanitize_quiz_text,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant_fixture(db):
    user_owner = User.objects.create_user(
        email="owner_s04@org.com",
        password="Password123!",
        first_name="Owner",
        last_name="Org",
    )
    user_teacher = User.objects.create_user(
        email="teacher_s04@org.com",
        password="Password123!",
        first_name="Teacher",
        last_name="Org",
    )
    user_student = User.objects.create_user(
        email="student_s04@org.com",
        password="Password123!",
        first_name="Student",
        last_name="Org",
    )
    user_outsider = User.objects.create_user(
        email="outsider_s04@other.com",
        password="Password123!",
        first_name="Outsider",
        last_name="Other",
    )

    org_a = Organization.objects.create(name="Org A Sprint 04", slug="org-a-s04")
    OrganizationMember.objects.create(organization=org_a, user=user_owner, role=RoleChoices.OWNER)
    OrganizationMember.objects.create(
        organization=org_a, user=user_teacher, role=RoleChoices.TEACHER
    )
    OrganizationMember.objects.create(
        organization=org_a, user=user_student, role=RoleChoices.STUDENT
    )

    org_b = Organization.objects.create(name="Org B Sprint 04", slug="org-b-s04")
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
def sample_document(db, tenant_fixture):
    org = tenant_fixture["org_a"]
    teacher = tenant_fixture["teacher"]

    doc = Document.objects.create(
        organization=org,
        owner=teacher,
        title="Cours d'Intelligence Artificielle Avancée",
        file_name="ai_advanced.pdf",
        file_type="pdf",
        file_size=2048,
        storage_key="test/ai_advanced.pdf",
        status=DocumentStatus.READY,
    )
    page = DocumentPage.objects.create(
        document=doc,
        page_number=1,
        text="Les mécanismes d'auto-attention pondèrent dynamiquement les représentations.",
    )
    DocumentChunk.objects.create(
        document=doc,
        page=page,
        chunk_index=0,
        content="L'auto-attention calcule des scores de similarité entre toutes les paires de tokens.",
        token_count=25,
        metadata={"chapter": "Attention", "section": "1.1"},
        embedding=[0.05] * 128,
    )
    return doc


@pytest.fixture
def sample_quiz_with_questions(db, tenant_fixture, sample_document):
    org = tenant_fixture["org_a"]
    teacher = tenant_fixture["teacher"]

    quiz = Quiz.objects.create(
        organization=org,
        created_by=teacher,
        document=sample_document,
        title="Évaluation Sommative Sprint 04",
        type=QuizType.EXAM,
        difficulty=DifficultyLevel.MEDIUM,
        passing_score_percentage=75,
    )

    q1 = QuizQuestion.objects.create(
        quiz=quiz,
        text="Quel est le rôle fondamental de la fonction Softmax dans un classifieur multi-classes ?",
        explanation="La fonction Softmax convertit un vecteur de logits réels en une distribution de probabilités sommant à 1.",
        difficulty=DifficultyLevel.MEDIUM,
        source="Section 1.2 : Fonctions d'activation",
        order=0,
    )
    a1_correct = QuizAnswer.objects.create(
        question=q1,
        text="Transformer les logits en distribution de probabilités",
        is_correct=True,
        order=0,
    )
    a1_wrong = QuizAnswer.objects.create(
        question=q1,
        text="Calculer la dérivée seconde de la fonction de coût",
        is_correct=False,
        order=1,
    )
    QuizAnswer.objects.create(
        question=q1,
        text="Initialiser les poids synaptiques de façon orthogonale",
        is_correct=False,
        order=2,
    )
    QuizAnswer.objects.create(
        question=q1,
        text="Éliminer les gradients qui s'annulent lors du passage arrière",
        is_correct=False,
        order=3,
    )

    q2 = QuizQuestion.objects.create(
        quiz=quiz,
        text="Quelle technique de régularisation permet de limiter le surapprentissage en pénalisant les grands poids ?",
        explanation="La régularisation L2 (Weight Decay) applique une pénalité quadratique sur la norme des poids pour favoriser des représentations plus diffuses.",
        difficulty=DifficultyLevel.HARD,
        source="Section 2.1 : Régularisation L2",
        order=1,
    )
    a2_correct = QuizAnswer.objects.create(
        question=q2, text="La régularisation L2 (Weight Decay)", is_correct=True, order=0
    )
    a2_wrong = QuizAnswer.objects.create(
        question=q2,
        text="L'augmentation non supervisée du taux d'apprentissage",
        is_correct=False,
        order=1,
    )
    QuizAnswer.objects.create(
        question=q2,
        text="La réduction du nombre d'époques d'entraînement à une seule",
        is_correct=False,
        order=2,
    )
    QuizAnswer.objects.create(
        question=q2,
        text="La suppression pure et simple des connexions résiduelles",
        is_correct=False,
        order=3,
    )

    return {
        "quiz": quiz,
        "q1": q1,
        "q2": q2,
        "a1_correct": a1_correct,
        "a1_wrong": a1_wrong,
        "a2_correct": a2_correct,
        "a2_wrong": a2_wrong,
    }


# =========================================================================
# 1. Validation Logic & Psychometric Robustness
# =========================================================================


class TestSprint04QuizQuestionValidator:
    def test_safe_boolean_parsing_handles_strings_and_numbers(self):
        assert parse_boolean_value(True) is True
        assert parse_boolean_value("true") is True
        assert parse_boolean_value("True") is True
        assert parse_boolean_value("1") is True
        assert parse_boolean_value(1) is True
        assert parse_boolean_value("oui") is True
        assert parse_boolean_value("صحيح") is True

        # Critical: "false" string must NEVER evaluate to True
        assert parse_boolean_value(False) is False
        assert parse_boolean_value("false") is False
        assert parse_boolean_value("False") is False
        assert parse_boolean_value("0") is False
        assert parse_boolean_value(0) is False
        assert parse_boolean_value("non") is False
        assert parse_boolean_value("خطأ") is False

    def test_boolean_string_false_in_question_does_not_mark_multiple_correct(self):
        validator = QuizQuestionValidator()
        raw = {
            "question": "Quel est le principe de la régression logistique binaire ?",
            "answers": [
                {
                    "text": "Prédire une probabilité d'appartenance à une classe",
                    "is_correct": "true",
                },
                {
                    "text": "Estimer une droite de régression sans fonction seuil",
                    "is_correct": "false",
                },
                {
                    "text": "Partitionner les données en k clusters centroïdes",
                    "is_correct": "false",
                },
                {
                    "text": "Construire un arbre binaire de décision par entropie",
                    "is_correct": "false",
                },
            ],
            "explanation": "La régression logistique utilise la sigmoïde pour modéliser une probabilité entre 0 et 1.",
            "difficulty": "MEDIUM",
            "source": "Chapitre 1 : Modèles linéaires",
        }
        validated = validator.validate_and_normalize(raw)
        assert sum(1 for a in validated["answers"] if a["is_correct"]) == 1
        assert validated["answers"][0]["is_correct"] is True
        assert validated["answers"][1]["is_correct"] is False

    def test_sanitize_quiz_text_strips_control_characters(self):
        raw = "Question avec\x00 caractères\x08 de contrôle\x1f et Unicode arabe : الذكاء الاصطناعي"
        cleaned = sanitize_quiz_text(raw)
        assert "\x00" not in cleaned
        assert "\x08" not in cleaned
        assert "\x1f" not in cleaned
        assert "الذكاء الاصطناعي" in cleaned

    def test_reject_question_text_too_short(self):
        validator = QuizQuestionValidator()
        raw = {
            "question": "Court ?",
            "answers": [
                {"text": "Opt A", "is_correct": True},
                {"text": "Opt B", "is_correct": False},
                {"text": "Opt C", "is_correct": False},
                {"text": "Opt D", "is_correct": False},
            ],
            "explanation": "Explication pédagogique suffisamment longue et détaillée.",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_info:
            validator.validate_and_normalize(raw)
        assert "trop court" in str(exc_info.value)

    def test_reject_tautological_or_lazy_explanations(self):
        validator = QuizQuestionValidator()
        raw = {
            "question": "Pourquoi la fonction ReLU est-elle populaire dans les réseaux profonds ?",
            "answers": [
                {
                    "text": "Elle évite la saturation du gradient pour les activations positives",
                    "is_correct": True,
                },
                {
                    "text": "Elle borne la sortie strictement dans l'intervalle [-1, 1]",
                    "is_correct": False,
                },
                {"text": "Elle est infiniment dérivable en zéro", "is_correct": False},
                {
                    "text": "Elle supprime le besoin de couches convolutionnelles",
                    "is_correct": False,
                },
            ],
            "explanation": "C'est la bonne réponse",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_info:
            validator.validate_and_normalize(raw)
        assert "tautologique" in str(exc_info.value)

    def test_reject_banned_meta_distractors(self):
        validator = QuizQuestionValidator()
        # Testing French meta-distractor
        raw_fr = {
            "question": "Quelles sont les propriétés d'un estimateur sans biais ?",
            "answers": [
                {
                    "text": "Son espérance mathématique est égale au paramètre cible",
                    "is_correct": True,
                },
                {
                    "text": "Sa variance tend vers l'infini avec la taille de l'échantillon",
                    "is_correct": False,
                },
                {
                    "text": "Sa distribution d'échantillonnage est obligatoirement normale",
                    "is_correct": False,
                },
                {"text": "Toutes les réponses ci-dessus", "is_correct": False},
            ],
            "explanation": "Un estimateur sans biais a une espérance égale à la valeur vraie du paramètre.",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_fr:
            validator.validate_and_normalize(raw_fr)
        assert "méta-distracteurs" in str(exc_fr.value)

        # Testing Arabic meta-distractor
        raw_ar = {
            "question": "ما هي خصائص خوارزمية البحث الخطي في المصفوفات غير المرتبة؟",
            "answers": [
                {"text": "تفحص العناصر تتابعياً حتى العثور على العنصر المطلوب", "is_correct": True},
                {"text": "تتطلب تعقيداً زمنياً لوغاريتمياً في أسوأ الحالات", "is_correct": False},
                {"text": "تعتمد دائماً على شجرة بحث ثنائية متوازنة مسبقاً", "is_correct": False},
                {"text": "كل ما سبق", "is_correct": False},
            ],
            "explanation": "تقوم خوارزمية البحث الخطي بالمرور على جميع عناصر المصفوفة تتابعياً للبحث عن القيمة المطلوبة.",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_ar:
            validator.validate_and_normalize(raw_ar)
        assert "méta-distracteurs" in str(exc_ar.value)

    def test_reject_duplicate_options_with_punctuation_variations(self):
        validator = QuizQuestionValidator()
        raw = {
            "question": "Quel est l'hyperparamètre contrôlant la taille des pas lors de la descente de gradient ?",
            "answers": [
                {"text": "Le taux d'apprentissage (Learning Rate)", "is_correct": True},
                {
                    "text": "Le taux d'apprentissage (Learning Rate).",
                    "is_correct": False,
                },  # duplicate with trailing dot
                {"text": "Le coefficient de moment de Nesterov", "is_correct": False},
                {"text": "La taille du mini-lot (Batch Size)", "is_correct": False},
            ],
            "explanation": "Le taux d'apprentissage détermine l'amplitude de chaque mise à jour des paramètres du modèle.",
        }
        with pytest.raises(InvalidQuizQuestionError) as exc_info:
            validator.validate_and_normalize(raw)
        assert "doublon" in str(exc_info.value)

    def test_payload_deduplicates_repeated_questions_in_same_quiz(self):
        validator = QuizQuestionValidator()
        payload = [
            {
                "question": "Quelle est l'unité de base d'un réseau convolutif pour traiter les images ?",
                "answers": [
                    {"text": "Le filtre de convolution 2D", "is_correct": True},
                    {"text": "La porte d'oubli de type LSTM", "is_correct": False},
                    {"text": "La tête d'attention multi-échelle", "is_correct": False},
                    {"text": "Le bloc résiduel dense 3D", "is_correct": False},
                ],
                "explanation": "Les filtres convolutifs balaient l'image pour extraire des motifs géométriques locaux.",
            },
            {
                # Duplicate question prompt
                "question": "Quelle est l'unité de base d'un réseau convolutif pour traiter les images ?",
                "answers": [
                    {"text": "Le filtre de convolution 2D", "is_correct": True},
                    {"text": "La porte d'oubli de type LSTM", "is_correct": False},
                    {"text": "La tête d'attention multi-échelle", "is_correct": False},
                    {"text": "Le bloc résiduel dense 3D", "is_correct": False},
                ],
                "explanation": "Les filtres convolutifs balaient l'image pour extraire des motifs géométriques locaux.",
            },
        ]
        validated = validator.validate_quiz_payload(payload)
        # Should keep only 1 question and drop the duplicate
        assert len(validated) == 1


# =========================================================================
# 2. Multilingual AI Quiz Generation
# =========================================================================


@pytest.mark.django_db
class TestSprint04MultilingualGeneration:
    def test_generate_french_quiz(self, sample_quiz_with_questions, sample_document):
        quiz = sample_quiz_with_questions["quiz"]
        gen_service = QuizGeneratorService()

        created = gen_service.generate_questions_for_quiz(
            quiz=quiz,
            document=sample_document,
            provider_name="mock",
            count=2,
            language="fr",
        )
        assert len(created) >= 2
        for q in created:
            assert len(q.text) >= 10
            assert q.answers.count() == 4
            assert q.answers.filter(is_correct=True).count() == 1
            assert len(q.explanation) >= 15

    def test_generate_arabic_quiz(self, sample_quiz_with_questions, sample_document):
        quiz = sample_quiz_with_questions["quiz"]
        quiz.title = "اختبار الذكاء الاصطناعي وتقنيات التعلم الآلي"
        quiz.save()

        gen_service = QuizGeneratorService()
        created = gen_service.generate_questions_for_quiz(
            quiz=quiz,
            document=sample_document,
            provider_name="mock",
            count=2,
            language="ar",
        )
        assert len(created) >= 2
        for q in created:
            # Verify Arabic content
            assert any("\u0600" <= c <= "\u06ff" for c in q.text)
            assert q.answers.count() == 4
            assert q.answers.filter(is_correct=True).count() == 1
            assert any("\u0600" <= c <= "\u06ff" for c in q.explanation)

    def test_generate_english_quiz(self, sample_quiz_with_questions, sample_document):
        quiz = sample_quiz_with_questions["quiz"]
        quiz.title = "Deep Learning Architecture Exam"
        quiz.save()

        gen_service = QuizGeneratorService()
        created = gen_service.generate_questions_for_quiz(
            quiz=quiz,
            document=sample_document,
            provider_name="mock",
            count=2,
            language="en",
        )
        assert len(created) >= 2
        for q in created:
            assert (
                "Transformer" in q.text
                or "optimization" in q.text
                or "loss" in q.text
                or len(q.text) > 10
            )
            assert q.answers.count() == 4
            assert q.answers.filter(is_correct=True).count() == 1


# =========================================================================
# 3. Attempt Scoring, Time Tracking & Double Submission Prevention
# =========================================================================


@pytest.mark.django_db
class TestSprint04AttemptEvaluationAndScoring:
    def test_unanswered_questions_evaluated_as_zero_points(
        self, sample_quiz_with_questions, tenant_fixture
    ):
        quiz = sample_quiz_with_questions["quiz"]
        student = tenant_fixture["student"]
        service = QuizAttemptService()

        attempt = service.start_attempt(quiz, student)

        # Answer only Q1, leave Q2 unanswered
        partial_answers = {
            str(sample_quiz_with_questions["q1"].id): str(
                sample_quiz_with_questions["a1_correct"].id
            ),
        }

        res = service.submit_attempt(attempt, partial_answers)
        assert res["total_questions"] == 2
        assert res["correct_answers_count"] == 1
        assert res["score"] == 50.0
        assert res["passed"] is False  # 50% < 75% threshold
        assert res["is_passed"] is False

        # Review contains both questions, Q2 marked incorrect
        reviews = res["questions_review"]
        assert len(reviews) == 2
        assert reviews[0]["is_correct"] is True
        assert reviews[0]["points_earned"] == 1.0
        assert reviews[1]["is_correct"] is False
        assert reviews[1]["points_earned"] == 0.0
        assert reviews[1]["chosen_answer_id"] is None

    def test_double_submission_raises_attempt_already_completed(
        self, sample_quiz_with_questions, tenant_fixture
    ):
        quiz = sample_quiz_with_questions["quiz"]
        student = tenant_fixture["student"]
        service = QuizAttemptService()

        attempt = service.start_attempt(quiz, student)
        answers = {
            str(sample_quiz_with_questions["q1"].id): str(
                sample_quiz_with_questions["a1_correct"].id
            ),
            str(sample_quiz_with_questions["q2"].id): str(
                sample_quiz_with_questions["a2_correct"].id
            ),
        }

        # First submission completes the attempt
        res1 = service.submit_attempt(attempt, answers)
        assert res1["score"] == 100.0
        assert attempt.completed_at is not None

        # Second submission must be rejected
        with pytest.raises(AttemptAlreadyCompletedError) as exc_info:
            service.submit_attempt(attempt, answers)
        assert "déjà été soumise" in str(exc_info.value)


# =========================================================================
# 4. Security, Secrecy & Tenant Isolation
# =========================================================================


@pytest.mark.django_db
class TestSprint04SecurityAndIsolation:
    def test_student_cannot_see_correct_answers_or_explanations_before_submission(
        self, api_client, sample_quiz_with_questions, tenant_fixture
    ):
        student = tenant_fixture["student"]
        quiz = sample_quiz_with_questions["quiz"]
        api_client.force_authenticate(user=student)

        res = api_client.get(f"/api/v1/quizzes/{quiz.id}/")
        assert res.status_code == status.HTTP_200_OK

        questions = res.data["questions"]
        assert len(questions) == 2

        for q in questions:
            # Explanation must be hidden for student during test
            assert q["explanation"] == ""
            for a in q["answers"]:
                # is_correct must NOT be present
                assert "is_correct" not in a

    def test_teacher_can_see_correct_answers_and_explanations(
        self, api_client, sample_quiz_with_questions, tenant_fixture
    ):
        teacher = tenant_fixture["teacher"]
        quiz = sample_quiz_with_questions["quiz"]
        api_client.force_authenticate(user=teacher)

        res = api_client.get(f"/api/v1/quizzes/{quiz.id}/")
        assert res.status_code == status.HTTP_200_OK

        questions = res.data["questions"]
        assert len(questions) == 2

        for q in questions:
            assert q["explanation"] != ""
            assert any(a.get("is_correct") is True for a in q["answers"])

    def test_submit_endpoint_returns_409_conflict_on_resubmission(
        self, api_client, sample_quiz_with_questions, tenant_fixture
    ):
        student = tenant_fixture["student"]
        quiz = sample_quiz_with_questions["quiz"]
        api_client.force_authenticate(user=student)

        # 1. Start attempt
        start_res = api_client.post(f"/api/v1/quizzes/{quiz.id}/start/")
        attempt_id = start_res.data["id"]

        submit_payload = {
            "attempt_id": attempt_id,
            "answers": {
                str(sample_quiz_with_questions["q1"].id): str(
                    sample_quiz_with_questions["a1_correct"].id
                ),
            },
        }

        # 2. First submission -> 200 OK
        first_submit = api_client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/", submit_payload, format="json"
        )
        assert first_submit.status_code == status.HTTP_200_OK

        # 3. Second submission on same attempt_id -> 409 Conflict
        second_submit = api_client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/", submit_payload, format="json"
        )
        assert second_submit.status_code == status.HTTP_409_CONFLICT
        assert second_submit.data["code"] == "attempt_already_completed"

    def test_student_cannot_generate_quiz_questions(
        self, api_client, sample_quiz_with_questions, tenant_fixture
    ):
        student = tenant_fixture["student"]
        quiz = sample_quiz_with_questions["quiz"]
        api_client.force_authenticate(user=student)

        payload = {"count": 3, "provider": "mock"}
        res = api_client.post(f"/api/v1/quizzes/{quiz.id}/generate/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_cross_tenant_document_cannot_be_used_to_generate_quiz(
        self, api_client, sample_quiz_with_questions, tenant_fixture
    ):
        teacher = tenant_fixture["teacher"]
        quiz = sample_quiz_with_questions["quiz"]
        api_client.force_authenticate(user=teacher)

        # Document belonging to org_b
        outsider_doc = Document.objects.create(
            organization=tenant_fixture["org_b"],
            owner=tenant_fixture["outsider"],
            title="Document Externe Secret",
            file_name="secret.pdf",
            file_type="pdf",
            file_size=1024,
            storage_key="test/secret.pdf",
            status=DocumentStatus.READY,
        )

        payload = {
            "count": 2,
            "document_id": str(outsider_doc.id),
            "provider": "mock",
        }
        res = api_client.post(f"/api/v1/quizzes/{quiz.id}/generate/", payload, format="json")
        assert res.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN)
