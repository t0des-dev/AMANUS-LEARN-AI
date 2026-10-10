
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.courses.models import Course, CourseLevel, CourseSection, CourseStatus
from apps.learning.models import (
    LearningPath,
    LearningPathStatus,
    LearningProgress,
)
from apps.learning.services.learning_engine import LearningEngine
from apps.organizations.models import Organization, OrganizationMember, RoleChoices
from apps.quizzes.models import (
    Quiz,
    QuizAnswer,
    QuizQuestion,
    QuizType,
)
from apps.quizzes.services import AttemptAlreadyCompletedError, QuizAttemptService

User = get_user_model()


class Sprint11LearningProgressionTests(APITestCase):
    """Exhaustive test suite for Sprint 11: Learning Progression, Resumption, and Recommendations."""

    def setUp(self):
        # 1. Main student user
        self.user = User.objects.create_user(
            email="alice.learner@amanus.test",
            password="securepassword123",
            first_name="Alice",
            last_name="Learner",
        )
        # 2. Second student user in the same org
        self.peer = User.objects.create_user(
            email="bob.peer@amanus.test",
            password="securepassword123",
            first_name="Bob",
            last_name="Peer",
        )
        # 3. Unauthorized stranger user (different org)
        self.stranger = User.objects.create_user(
            email="stranger.user@amanus.test",
            password="securepassword123",
            first_name="Charlie",
            last_name="Stranger",
        )

        # Organizations
        self.org = Organization.objects.create(name="Amanus Academy", slug="amanus-academy")
        self.other_org = Organization.objects.create(name="External Academy", slug="external-academy")

        OrganizationMember.objects.create(organization=self.org, user=self.user, role=RoleChoices.STUDENT)
        OrganizationMember.objects.create(organization=self.org, user=self.peer, role=RoleChoices.STUDENT)
        OrganizationMember.objects.create(
            organization=self.other_org, user=self.stranger, role=RoleChoices.STUDENT
        )

        # Course with 3 sections
        self.course = Course.objects.create(
            organization=self.org,
            created_by=self.user,
            title="Introduction aux Réseaux de Neurones",
            level=CourseLevel.BEGINNER,
            status=CourseStatus.PUBLISHED,
        )
        self.sec1 = CourseSection.objects.create(
            course=self.course,
            title="1. Le Perceptron Simple",
            order=1,
        )
        self.sec2 = CourseSection.objects.create(
            course=self.course,
            title="2. Rétropropagation du Gradient",
            order=2,
        )
        self.sec3 = CourseSection.objects.create(
            course=self.course,
            title="3. Fonctions d'Activation et Softmax",
            order=3,
        )

        # Quiz with 2 questions
        self.quiz = Quiz.objects.create(
            organization=self.org,
            course=self.course,
            title="QCM - Évaluation Réseaux de Neurones",
            type=QuizType.TRAINING,
            passing_score_percentage=70,
        )
        self.q1 = QuizQuestion.objects.create(
            quiz=self.quiz,
            text="Quelle fonction d'activation est généralement utilisée en classification multiclasse ?",
            explanation="La fonction Softmax transforme un vecteur de logits en probabilités normalisées.",
            source="Section 3: Fonctions d'activation, paragraphe 2",
            order=0,
        )
        self.q1_ans_correct = QuizAnswer.objects.create(
            question=self.q1, text="Softmax", is_correct=True, order=0
        )
        self.q1_ans_wrong = QuizAnswer.objects.create(
            question=self.q1, text="Sigmoïde linéaire", is_correct=False, order=1
        )
        self.q1_ans_wrong2 = QuizAnswer.objects.create(
            question=self.q1, text="ReLU saturée", is_correct=False, order=2
        )
        self.q1_ans_wrong3 = QuizAnswer.objects.create(
            question=self.q1, text="Tangente constante", is_correct=False, order=3
        )

        self.q2 = QuizQuestion.objects.create(
            quiz=self.quiz,
            text="Quel algorithme calcule le gradient de l'erreur par rapport à chaque poids ?",
            explanation="La rétropropagation utilise la règle de dérivation en chaîne (chain rule).",
            source="Section 2: Rétropropagation du gradient",
            order=1,
        )
        self.q2_ans_correct = QuizAnswer.objects.create(
            question=self.q2, text="La rétropropagation du gradient", is_correct=True, order=0
        )
        self.q2_ans_wrong = QuizAnswer.objects.create(
            question=self.q2, text="La descente aléatoire", is_correct=False, order=1
        )
        self.q2_ans_wrong2 = QuizAnswer.objects.create(
            question=self.q2, text="L'inversion matricielle directe", is_correct=False, order=2
        )
        self.q2_ans_wrong3 = QuizAnswer.objects.create(
            question=self.q2, text="Le tri topologique glouton", is_correct=False, order=3
        )

        # JWT auth headers
        token = RefreshToken.for_user(self.user)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {token.access_token}"}

        peer_token = RefreshToken.for_user(self.peer)
        self.peer_headers = {"HTTP_AUTHORIZATION": f"Bearer {peer_token.access_token}"}

        stranger_token = RefreshToken.for_user(self.stranger)
        self.stranger_headers = {"HTTP_AUTHORIZATION": f"Bearer {stranger_token.access_token}"}

        self.engine = LearningEngine()

    # -------------------------------------------------------------------------
    # 1. Démarrage et mise à jour d'une progression
    # -------------------------------------------------------------------------
    def test_progression_init_and_monotonic_updates(self):
        """Validates starting a progression and monotonically updating progress."""
        progress, path = self.engine.record_section_progress(
            user=self.user,
            section=self.sec1,
            completion_percent=35.0,
            last_position=350,
            is_completed=False,
        )
        self.assertEqual(progress.completion_percent, 35.0)
        self.assertFalse(progress.is_completed)
        self.assertIsNone(progress.completed_at)
        self.assertEqual(progress.last_position, 350)
        self.assertEqual(path.status, LearningPathStatus.IN_PROGRESS)
        self.assertIsNotNone(path.started_at)
        self.assertIsNone(path.completed_at)

        # Submitting lower percentage (e.g. re-viewing top of page) keeps max percent
        progress_updated, path_updated = self.engine.record_section_progress(
            user=self.user,
            section=self.sec1,
            completion_percent=20.0,
            last_position=100,
            is_completed=False,
        )
        self.assertEqual(progress_updated.completion_percent, 35.0)
        self.assertEqual(progress_updated.last_position, 100)
        self.assertFalse(progress_updated.is_completed)

    # -------------------------------------------------------------------------
    # 2. Règle de complétion : distinction entre consulté et complété
    # -------------------------------------------------------------------------
    def test_lesson_completion_rule_viewed_vs_completed(self):
        """Ensures viewing a lesson does NOT mark it complete without explicit 100% or is_completed flag."""
        # 1. User merely visits section 1 and scrolls partially
        url = f"/api/v1/learning/sections/{self.sec1.id}/complete/"
        res_view = self.client.post(
            url,
            {"completion_percent": 45.0, "last_position": 800, "is_completed": False},
            format="json",
            **self.auth_headers,
        )
        self.assertEqual(res_view.status_code, status.HTTP_200_OK)
        self.assertFalse(res_view.data["progress"]["is_completed"])
        self.assertIsNone(res_view.data["progress"]["completed_at"])
        self.assertIsNotNone(res_view.data["progress"]["last_viewed_at"])

        # Course is IN_PROGRESS (45 / 3 = 15% progress)
        self.assertEqual(res_view.data["course_status"], LearningPathStatus.IN_PROGRESS)
        self.assertEqual(res_view.data["course_progress"], 15.0)

        # 2. User explicitly declares section completed
        res_complete = self.client.post(
            url,
            {"is_completed": True},
            format="json",
            **self.auth_headers,
        )
        self.assertEqual(res_complete.status_code, status.HTTP_200_OK)
        self.assertTrue(res_complete.data["progress"]["is_completed"])
        self.assertIsNotNone(res_complete.data["progress"]["completed_at"])
        self.assertEqual(res_complete.data["progress"]["completion_percent"], 100.0)

    # -------------------------------------------------------------------------
    # 3. Reprise après une nouvelle session (continue_learning)
    # -------------------------------------------------------------------------
    def test_resume_learning_points_to_first_incomplete_section(self):
        """Ensures continue_learning points to next incomplete section with preserved last_position."""
        # Complete Section 1
        self.engine.record_section_progress(
            user=self.user,
            section=self.sec1,
            completion_percent=100.0,
            is_completed=True,
        )
        # Partially read Section 2 (position 950)
        self.engine.record_section_progress(
            user=self.user,
            section=self.sec2,
            completion_percent=60.0,
            last_position=950,
            is_completed=False,
        )

        dashboard = self.engine.get_student_dashboard(self.user)
        cont = dashboard["continue_learning"]

        self.assertIsNotNone(cont)
        self.assertEqual(cont["course_id"], str(self.course.id))
        self.assertEqual(cont["section_id"], str(self.sec2.id))
        self.assertEqual(cont["section_title"], self.sec2.title)
        self.assertEqual(cont["last_position"], 950)
        self.assertEqual(cont["section_completion_percent"], 60.0)
        self.assertFalse(cont["is_completed"])

    # -------------------------------------------------------------------------
    # 4. Calcul déterministe des cours commencés et terminés
    # -------------------------------------------------------------------------
    def test_course_status_transitions_deterministically(self):
        """Verifies deterministic transitions: NOT_STARTED -> IN_PROGRESS -> COMPLETED."""
        path = LearningPath.objects.create(
            user=self.user,
            course=self.course,
            status=LearningPathStatus.NOT_STARTED,
        )
        self.assertEqual(path.status, LearningPathStatus.NOT_STARTED)
        self.assertEqual(path.progress, 0.0)

        # Complete section 1 (33.3%)
        self.engine.record_section_progress(self.user, self.sec1, is_completed=True)
        path.refresh_from_db()
        self.assertEqual(path.status, LearningPathStatus.IN_PROGRESS)
        self.assertEqual(path.progress, 33.3)

        # Complete section 2 (66.7%)
        self.engine.record_section_progress(self.user, self.sec2, is_completed=True)
        path.refresh_from_db()
        self.assertEqual(path.status, LearningPathStatus.IN_PROGRESS)
        self.assertEqual(path.progress, 66.7)

        # Complete section 3 (100.0%)
        self.engine.record_section_progress(self.user, self.sec3, is_completed=True)
        path.refresh_from_db()
        self.assertEqual(path.status, LearningPathStatus.COMPLETED)
        self.assertEqual(path.progress, 100.0)
        self.assertIsNotNone(path.completed_at)

        # When all courses are completed, continue_learning gracefully returns None
        dashboard = self.engine.get_student_dashboard(self.user)
        self.assertIsNone(dashboard["continue_learning"])

    # -------------------------------------------------------------------------
    # 5. Calcul des scores côté serveur (évaluation serveur)
    # -------------------------------------------------------------------------
    def test_quiz_score_calculated_strictly_server_side(self):
        """Ensures browser cannot tamper with scores: evaluation is 100% computed server-side."""
        service = QuizAttemptService()
        attempt = service.start_attempt(self.quiz, self.user)

        # Submit answers: Q1 correct, Q2 wrong
        answers = {
            str(self.q1.id): str(self.q1_ans_correct.id),
            str(self.q2.id): str(self.q2_ans_wrong.id),
        }

        # Client attempt payload does not specify score
        evaluation = service.submit_attempt(attempt, submitted_answers=answers)
        self.assertEqual(evaluation["score"], 50.0)
        self.assertEqual(evaluation["total_questions"], 2)
        self.assertEqual(evaluation["correct_answers_count"], 1)
        self.assertFalse(evaluation["passed"])

        # Check in DB
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 50.0)
        self.assertFalse(attempt.passed)
        self.assertIsNotNone(attempt.completed_at)

    # -------------------------------------------------------------------------
    # 6. Distinction entre meilleur score, dernier score et historique
    # -------------------------------------------------------------------------
    def test_quiz_history_distinguishes_best_score_and_latest_score(self):
        """Verifies QuizResultsHistoryView clearly exposes best_score vs latest_score vs attempts list."""
        service = QuizAttemptService()

        # Attempt 1: 50%
        att1 = service.start_attempt(self.quiz, self.user)
        service.submit_attempt(
            att1,
            {
                str(self.q1.id): str(self.q1_ans_correct.id),
                str(self.q2.id): str(self.q2_ans_wrong.id),
            },
        )

        # Attempt 2: 100%
        att2 = service.start_attempt(self.quiz, self.user)
        service.submit_attempt(
            att2,
            {
                str(self.q1.id): str(self.q1_ans_correct.id),
                str(self.q2.id): str(self.q2_ans_correct.id),
            },
        )

        # Attempt 3: 0% (retake went poorly)
        att3 = service.start_attempt(self.quiz, self.user)
        service.submit_attempt(
            att3,
            {
                str(self.q1.id): str(self.q1_ans_wrong.id),
                str(self.q2.id): str(self.q2_ans_wrong.id),
            },
        )

        url = f"/api/v1/quizzes/{self.quiz.id}/results/"
        res = self.client.get(url, **self.auth_headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data["total_attempts"], 3)
        self.assertEqual(res.data["best_score"], 100.0)
        self.assertEqual(res.data["latest_score"], 0.0)
        self.assertEqual(res.data["best_attempt_id"], str(att2.id))
        self.assertEqual(res.data["latest_attempt_id"], str(att3.id))
        self.assertTrue(res.data["has_passed"])
        self.assertEqual(res.data["average_score"], 50.0)

    # -------------------------------------------------------------------------
    # 7. Recommandations après une réponse incorrecte (notions à réviser)
    # -------------------------------------------------------------------------
    def test_recommendations_after_failed_quiz_attempt(self):
        """Failed evaluation (<60%) produces targeted weak topic & revision recommendation."""
        service = QuizAttemptService()
        att = service.start_attempt(self.quiz, self.user)
        service.submit_attempt(
            att,
            {
                str(self.q1.id): str(self.q1_ans_wrong.id),
                str(self.q2.id): str(self.q2_ans_wrong.id),
            },
        )

        dashboard = self.engine.get_student_dashboard(self.user)

        # Weak topic detected
        weak_topics = dashboard["weak_topics"]
        self.assertTrue(any(self.quiz.title in wt["section_title"] for wt in weak_topics))

        # Recommended revision present with reason
        revisions = dashboard["recommended_revision"]
        self.assertTrue(
            any(
                r["type"] == "weak_topic" and "seuil de validation" in r["reason"]
                for r in revisions
            )
        )

    # -------------------------------------------------------------------------
    # 8. Comportement sans historique (utilisateur débutant / état vide)
    # -------------------------------------------------------------------------
    def test_clean_empty_state_without_user_history(self):
        """A brand new learner gets coherent zeroed stats, None continue_learning, and no fake data."""
        dashboard = self.engine.get_student_dashboard(self.peer)

        self.assertEqual(dashboard["stats"]["total_study_time_seconds"], 0)
        self.assertEqual(dashboard["stats"]["courses_in_progress"], 0)
        self.assertEqual(dashboard["stats"]["courses_completed"], 0)
        self.assertEqual(dashboard["stats"]["total_enrolled_courses"], 0)
        self.assertEqual(dashboard["stats"]["completed_sections_count"], 0)
        self.assertIsNone(dashboard["stats"]["average_score"])

        self.assertIsNone(dashboard["continue_learning"])
        self.assertEqual(dashboard["weak_topics"], [])
        self.assertEqual(dashboard["recent_activity"], [])
        self.assertEqual(dashboard["recent_quiz_results"], [])
        self.assertEqual(dashboard["recommended_revision"], [])

    # -------------------------------------------------------------------------
    # 9. Concurrence et idempotence des requêtes
    # -------------------------------------------------------------------------
    def test_idempotent_section_completion_and_attempt_locking(self):
        """Repeated identical completion requests produce identical state without duplicate records."""
        # 1. Idempotent section completion
        for _ in range(3):
            prog, path = self.engine.record_section_progress(
                user=self.user,
                section=self.sec1,
                completion_percent=100.0,
                last_position=500,
                is_completed=True,
            )
            self.assertEqual(prog.completion_percent, 100.0)
            self.assertTrue(prog.is_completed)

        # Exactly 1 LearningProgress record created
        count = LearningProgress.objects.filter(user=self.user, section=self.sec1).count()
        self.assertEqual(count, 1)

        # 2. Resubmitting an already completed quiz attempt is blocked with 409 Conflict
        service = QuizAttemptService()
        att = service.start_attempt(self.quiz, self.user)
        service.submit_attempt(att, {str(self.q1.id): str(self.q1_ans_correct.id)})

        # Second submission raises AttemptAlreadyCompletedError
        with self.assertRaises(AttemptAlreadyCompletedError):
            service.submit_attempt(att, {str(self.q1.id): str(self.q1_ans_correct.id)})

    # -------------------------------------------------------------------------
    # 10. Isolation multi-tenant et permissions inter-utilisateurs
    # -------------------------------------------------------------------------
    def test_tenant_and_cross_user_isolation(self):
        """Users cannot access or modify each other's progress or attempts."""
        # Stranger (external org) cannot access course progress
        url_prog = f"/api/v1/learning/courses/{self.course.id}/progress/"
        res_stranger = self.client.get(url_prog, **self.stranger_headers)
        self.assertEqual(res_stranger.status_code, status.HTTP_403_FORBIDDEN)

        # Stranger cannot complete a section in another tenant
        url_complete = f"/api/v1/learning/sections/{self.sec1.id}/complete/"
        res_stranger_post = self.client.post(
            url_complete, {"is_completed": True}, format="json", **self.stranger_headers
        )
        self.assertEqual(res_stranger_post.status_code, status.HTTP_403_FORBIDDEN)

        # Peer cannot access quiz attempt belonging to Alice
        service = QuizAttemptService()
        att = service.start_attempt(self.quiz, self.user)
        url_submit = f"/api/v1/quizzes/{self.quiz.id}/submit/"
        # Peer tries to submit attempt of Alice
        res_peer_tamper = self.client.post(
            url_submit,
            {"attempt_id": str(att.id), "answers": {}},
            format="json",
            **self.peer_headers,
        )
        self.assertEqual(res_peer_tamper.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 11. Gestion des contenus modifiés ou supprimés
    # -------------------------------------------------------------------------
    def test_robustness_when_course_or_sections_are_deleted(self):
        """Dashboard handles orphaned sections or deleted courses without crashing."""
        # Record progress on course
        self.engine.record_section_progress(
            user=self.user,
            section=self.sec1,
            completion_percent=50.0,
            score=40.0,
        )

        # Delete section 1
        self.sec1.delete()

        # Engine still handles dashboard gracefully without 500 error
        dashboard = self.engine.get_student_dashboard(self.user)
        self.assertIsInstance(dashboard, dict)
        self.assertIn("stats", dashboard)

    # -------------------------------------------------------------------------
    # 12. Pagination de l'historique des quiz
    # -------------------------------------------------------------------------
    def test_user_quiz_history_paginated_endpoint(self):
        """GET /api/v1/quizzes/history/ correctly paginates user attempts."""
        service = QuizAttemptService()
        for i in range(5):
            att = service.start_attempt(self.quiz, self.user)
            service.submit_attempt(
                att,
                {
                    str(self.q1.id): str(self.q1_ans_correct.id),
                    str(self.q2.id): str(self.q2_ans_wrong.id),
                },
            )

        url = "/api/v1/quizzes/history/?page=1&page_size=3"
        res = self.client.get(url, **self.auth_headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_count"], 5)
        self.assertEqual(res.data["page"], 1)
        self.assertEqual(res.data["page_size"], 3)
        self.assertEqual(len(res.data["results"]), 3)
