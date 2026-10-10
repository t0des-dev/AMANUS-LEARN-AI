import json
from unittest.mock import MagicMock, patch

import pytest

from apps.ai.services import (
    AIResponse,
    MockAIProvider,
    PedagogicalBlueprint,
    PedagogicalBlueprintService,
    PedagogicalBlueprintValidator,
    PedagogicalConsistencyValidator,
    PromptService,
)
from apps.ai.services.generators.summary_generator import SummaryGenerator
from apps.ai.services.pedagogical_blueprint import InvalidPedagogicalBlueprintError
from apps.audio.services.script_generator import PedagogicalScriptGenerator
from apps.courses.models import Course, CourseLevel, CourseSection
from apps.documents.models import Document
from apps.ingestion.models import DocumentChunk
from apps.organizations.models import Organization
from apps.quizzes.models import DifficultyLevel, Quiz, QuizType
from apps.quizzes.services.generator import QuizGeneratorService
from apps.quizzes.services.validator import InvalidQuizQuestionError, QuizQuestionValidator


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Amanus Pedagogical Org", slug="amanus-pedagogical-org")


@pytest.fixture
def sample_document(db, org):
    doc = Document.objects.create(
        organization=org,
        title="Architecture des Microservices et Conteneurs",
        file_name="microservices_guide.pdf",
        file_type="pdf",
        file_size=2048,
        storage_key="docs/microservices_guide.pdf",
        language="fr",
    )
    DocumentChunk.objects.create(
        document=doc,
        chunk_index=0,
        content=(
            "Les microservices constituent une approche architecturale logicielle où une application "
            "est structurée comme un ensemble de services faiblement couplés. Chaque microservice est "
            "autonome, déployable indépendamment et communique via des API légères comme REST ou gRPC. "
            "Docker et Kubernetes permettent d'orchestrer ces conteneurs en production avec haute disponibilité."
        ),
        metadata={"chapter": "Chapitre 1", "section": "Introduction aux Microservices"},
    )
    DocumentChunk.objects.create(
        document=doc,
        chunk_index=1,
        content=(
            "L'un des défis majeurs réside dans la gestion des transactions distribuées. "
            "Le pattern Saga permet de coordonner les transactions à travers des événements compensatoires "
            "plutôt que d'utiliser des verrous distribués à deux phases (2PC). "
            "La résilience est renforcée par des disjoncteurs (Circuit Breaker) comme Resilience4j."
        ),
        metadata={"chapter": "Chapitre 2", "section": "Patterns de Résilience et Cohérence"},
    )
    return doc


@pytest.fixture
def sample_course(db, org, sample_document):
    course = Course.objects.create(
        organization=org,
        document=sample_document,
        title="Architecture des Microservices et Conteneurs",
        description="Formation complète sur la conception et l'orchestration des microservices.",
        level=CourseLevel.BEGINNER,
        language="fr",
    )
    CourseSection.objects.create(
        course=course,
        title="Introduction aux Microservices",
        order=0,
        content="Les microservices séparent les responsabilités en composants autonomes communicant par API REST.",
        summary="Définition des microservices, autonomie de déploiement et communication inter-services.",
        objectives=[
            {"objective": "Comprendre les principes d'une architecture orientée microservices."},
            {"objective": "Identifier les avantages du découplage de services."},
        ],
    )
    CourseSection.objects.create(
        course=course,
        title="Patterns de Résilience et Cohérence",
        order=1,
        content="Mise en œuvre du pattern Saga et du circuit breaker pour garantir la tolérance aux pannes.",
        summary="Gestion des transactions distribuées via le pattern Saga et disjoncteurs logiciels.",
        objectives=[
            {"objective": "Appliquer le pattern Saga pour les transactions distribuées."},
            {"objective": "Configurer un circuit breaker pour prévenir les cascades de pannes."},
        ],
    )
    return course


class TestPedagogicalBlueprint:
    """Verifies schema validation, serialization, and derivation of PedagogicalBlueprint."""

    def test_blueprint_schema_and_serialization(self):
        blueprint = PedagogicalBlueprint(
            title="Introduction au Deep Learning",
            subject="Intelligence Artificielle",
            target_audience="Ingénieurs débutants",
            level="BEGINNER",
            prerequisites=["Algèbre linéaire", "Python de base"],
            learning_objectives=[
                {
                    "id": "obj-1",
                    "taxonomy_level": "Comprendre",
                    "description": "Comprendre le fonctionnement d'un neurone artificiel",
                    "source_ref": "[1]",
                }
            ],
            key_concepts=[
                {
                    "term": "Rétropropagation",
                    "canonical_definition": "Algorithme d'optimisation calculant le gradient de l'erreur",
                    "importance": "CORE",
                    "source_ref": "[1]",
                }
            ],
            sections_outline=[
                {
                    "order": 1,
                    "title": "Perceptron et fonctions d'activation",
                    "key_explanation": "Étude du modèle élémentaire",
                    "source_facts": ["Modèle linéaire de Rosenblatt"],
                    "pedagogical_examples": ["Classification binaire"],
                    "summary": "Introduction au perceptron",
                    "estimated_minutes": 15,
                }
            ],
            key_takeaways=["Linéarité", "Non-linéarité"],
        )

        data = blueprint.to_dict()
        assert data["version"] == "blueprint-v1.0"
        assert data["title"] == "Introduction au Deep Learning"
        assert len(data["learning_objectives"]) == 1
        assert data["learning_objectives"][0]["taxonomy_level"] == "Comprendre"
        assert len(data["key_concepts"]) == 1
        assert data["key_concepts"][0]["term"] == "Rétropropagation"
        assert len(blueprint.sections) == 1

    def test_blueprint_validator_success(self):
        validator = PedagogicalBlueprintValidator()
        raw_payload = {
            "title": "Bases de Python",
            "subject": "Programmation",
            "target_audience": "Débutants",
            "level": "BEGINNER",
            "learning_objectives": [
                {"id": "o1", "description": "Maîtriser les boucles", "taxonomy_level": "Appliquer"}
            ],
            "key_concepts": [
                {"term": "Boucle for", "canonical_definition": "Itération sur une séquence", "importance": "CORE"}
            ],
            "sections_outline": [
                {"order": 1, "title": "Syntaxe de base", "key_explanation": "Variables et types", "summary": "Bases"}
            ],
        }

        blueprint = validator.validate_and_build(raw_payload)
        assert blueprint.title == "Bases de Python"
        assert len(blueprint.learning_objectives) == 1
        assert len(blueprint.key_concepts) == 1
        assert len(blueprint.sections) == 1

    def test_blueprint_validator_rejects_missing_fields(self):
        validator = PedagogicalBlueprintValidator()
        # Missing title
        invalid_payload = {"level": "BEGINNER"}
        with pytest.raises(InvalidPedagogicalBlueprintError, match="Titre du blueprint manquant"):
            validator.validate_and_normalize(invalid_payload)

    def test_derive_blueprint_from_course_without_extra_llm(self, sample_course):
        service = PedagogicalBlueprintService()
        blueprint = service.derive_from_course(sample_course)

        assert blueprint.title == sample_course.title
        assert blueprint.level == CourseLevel.BEGINNER
        assert len(blueprint.sections) == 2
        assert len(blueprint.learning_objectives) >= 2
        # Key concepts derived from sections and summaries
        assert len(blueprint.key_concepts) >= 2
        concept_terms = [c["term"].lower() for c in blueprint.key_concepts]
        assert any("microservices" in t for t in concept_terms)


class TestMultiLevelSummaryGeneration:
    """Verifies generation and prompting for very_short, synthetic, and detailed summaries."""

    def test_summary_prompt_granularity(self):
        prompt_svc = PromptService()

        # Very short prompt
        _, prompt_vs, ver_vs = prompt_svc.get_summary_prompt(
            document_title="Guide DevOps",
            context="Texte source",
            language="fr",
            summary_level="very_short",
        )
        assert "100 mots" in prompt_vs
        assert "Point essentiel" in prompt_vs
        assert "very_short" in ver_vs

        # Synthetic prompt (default)
        _, prompt_syn, ver_syn = prompt_svc.get_summary_prompt(
            document_title="Guide DevOps",
            context="Texte source",
            language="fr",
            summary_level="synthetic",
        )
        assert "2-3 paragraphes" in prompt_syn
        assert ver_syn == "summary-v1.0"

        # Detailed prompt
        _, prompt_det, ver_det = prompt_svc.get_summary_prompt(
            document_title="Guide DevOps",
            context="Texte source",
            language="fr",
            summary_level="detailed",
        )
        assert "détaillé" in prompt_det.lower()
        assert "detailed" in ver_det

    def test_summary_generator_passes_summary_level(self, sample_document):
        provider = MockAIProvider()
        generator = SummaryGenerator()

        result, ai_resp, prompt_ver = generator.generate(
            document=sample_document,
            provider=provider,
            summary_level="very_short",
        )
        assert prompt_ver.startswith("summary-very_short")
        assert "overview" in result
        assert ai_resp.input_tokens > 0


class TestQuizPedagogicalAlignmentAndWarnings:
    """Verifies grounded quiz generation, objective mapping, and warning handling."""

    def test_quiz_generator_integrates_blueprint_and_emits_warnings_on_short_text(
        self, db, org, sample_course
    ):
        short_doc = Document.objects.create(
            organization=org,
            title="Mémo Bref",
            file_name="memo.pdf",
            file_type="pdf",
            file_size=512,
            storage_key="docs/memo.pdf",
            language="fr",
        )
        DocumentChunk.objects.create(
            document=short_doc,
            chunk_index=0,
            content="Docker permet d'isoler des processus dans des conteneurs légers.",
        )

        quiz = Quiz.objects.create(
            organization=org,
            course=sample_course,
            document=short_doc,
            title="Évaluation Docker",
            difficulty=DifficultyLevel.MEDIUM,
            type=QuizType.TRAINING,
        )

        valid_quiz_json = {
            "questions": [
                {
                    "question": "Quel est le rôle principal d'un conteneur Docker ?",
                    "answers": [
                        {"text": "Isoler des processus de manière légère", "is_correct": True},
                        {"text": "Émuler un processeur physique", "is_correct": False},
                        {"text": "Remplacer le noyau du système d'exploitation", "is_correct": False},
                        {"text": "Compiler du code machine en temps réel", "is_correct": False},
                    ],
                    "explanation": "Docker isole les processus au niveau de l'espace utilisateur sans émulation matérielle [1].",
                    "difficulty": "MEDIUM",
                    "source": "Mémo Bref",
                }
            ]
        }

        mock_provider = MockAIProvider()
        mock_provider.generate = MagicMock(
            return_value=AIResponse(
                content=json.dumps(valid_quiz_json),
                parsed_json=valid_quiz_json,
                input_tokens=100,
                output_tokens=80,
            )
        )

        with patch("apps.quizzes.services.generator.get_ai_provider", return_value=mock_provider):
            gen_service = QuizGeneratorService()
            questions = gen_service.generate_questions_for_quiz(
                quiz=quiz,
                document=short_doc,
                count=5,  # Requested 5, but source is short and model generates 1
            )

            assert len(questions) == 1
            assert questions[0].answers.count() == 4
            assert hasattr(questions, "warnings")
            assert len(questions.warnings) >= 1
            assert any("restreint" in w.lower() or "validées" in w.lower() for w in questions.warnings)

    def test_quiz_validator_rejects_tautological_and_meta_distractors(self):
        validator = QuizQuestionValidator()

        # Reject "All of the above"
        payload_meta = {
            "question": "Quelle est la caractéristique d'un microservice ?",
            "answers": [
                {"text": "Autonomie de déploiement", "is_correct": True},
                {"text": "Communication par API", "is_correct": False},
                {"text": "Base de données dédiée", "is_correct": False},
                {"text": "Toutes les réponses", "is_correct": False},
            ],
            "explanation": "Les microservices sont modulaires et communicants.",
        }
        with pytest.raises(InvalidQuizQuestionError, match="méta-distracteurs"):
            validator.validate_and_normalize(payload_meta)

        # Reject tautological explanation
        payload_tauto = {
            "question": "Quelle est la caractéristique d'un microservice ?",
            "answers": [
                {"text": "Autonomie de déploiement", "is_correct": True},
                {"text": "Dépendance circulaire", "is_correct": False},
                {"text": "Monolithe partagé", "is_correct": False},
                {"text": "Code spaghetti", "is_correct": False},
            ],
            "explanation": "C'est la bonne réponse.",
        }
        with pytest.raises(InvalidQuizQuestionError, match="tautologique"):
            validator.validate_and_normalize(payload_tauto)


class TestAudioScriptSpeechAdaptation:
    """Verifies that audio scripts proscribe visual cues and convert markdown tables for listening."""

    def test_clean_markdown_for_speech_strips_visual_cues(self):
        generator = PedagogicalScriptGenerator()
        raw_text = (
            "Comme illustré ci-dessus, l'architecture microservices offre une grande flexibilité. "
            "Voir le tableau ci-contre pour comparer REST et gRPC. "
            "Dans le schéma ci-dessous, observez les flux de messages asynchrones."
        )

        cleaned = generator.clean_markdown_for_speech(raw_text, language="fr")

        assert "comme illustré" not in cleaned.lower()
        assert "ci-dessus" not in cleaned.lower()
        assert "le tableau ci-contre" not in cleaned.lower()
        assert "schéma ci-dessous" not in cleaned.lower()

    def test_clean_markdown_for_speech_reformulates_tables(self):
        generator = PedagogicalScriptGenerator()
        table_text = (
            "Comparatif des protocoles :\n\n"
            "| Protocole | Type | Usage |\n"
            "|---|---|---|\n"
            "| REST | HTTP/JSON | Communication externe |\n"
            "| gRPC | HTTP/2 Protobuf | Communication interne |\n"
        )

        cleaned = generator.clean_markdown_for_speech(table_text, language="fr")

        assert "|" not in cleaned
        assert "REST" in cleaned
        assert "gRPC" in cleaned


class TestPedagogicalConsistencyValidator:
    """Verifies cross-modal coherence checks and bounded retry remediation."""

    def test_validate_summary_alignment_success(self, sample_course):
        validator = PedagogicalConsistencyValidator(min_concept_coverage=0.40)
        blueprint = PedagogicalBlueprintService().derive_from_course(sample_course)

        valid_summary = (
            "Ce cours explore les microservices, leur autonomie et leurs protocoles de communication. "
            "Nous abordons également la résilience, le pattern saga et les disjoncteurs pour sécuriser "
            "les transactions distribuées."
        )

        report = validator.validate_course_and_summary_alignment(blueprint, valid_summary)
        assert report.is_valid is True
        assert report.score >= 0.40
        assert len(report.covered_concepts) >= 1

    def test_validate_summary_alignment_detects_insufficient_coverage(self, sample_course):
        validator = PedagogicalConsistencyValidator(min_concept_coverage=0.50)
        blueprint = PedagogicalBlueprintService().derive_from_course(sample_course)

        poor_summary = "Ceci est un texte parlant uniquement de cuisine italienne et de pâtes fraîches."

        report = validator.validate_course_and_summary_alignment(blueprint, poor_summary)
        assert report.is_valid is False
        assert any("Couverture conceptuelle insuffisante" in issue for issue in report.issues)

    def test_validate_audio_alignment_flags_forbidden_visual_cues(self, sample_course):
        validator = PedagogicalConsistencyValidator()
        blueprint = PedagogicalBlueprintService().derive_from_course(sample_course)

        script_with_visuals = (
            "Bonjour à tous. Voir ci-dessus la figure expliquant les microservices. "
            "Comme illustré ci-dessous, les conteneurs sont isolés."
        )

        report = validator.validate_course_and_audio_alignment(blueprint, script_with_visuals)
        assert report.is_valid is False
        assert any("Référence visuelle inadaptée" in issue for issue in report.issues)

    def test_validate_slides_alignment_checks_structure_and_density(self, sample_course):
        validator = PedagogicalConsistencyValidator()
        blueprint = PedagogicalBlueprintService().derive_from_course(sample_course)

        slides_data = [
            {
                "title": "Introduction aux Microservices",
                "bullets": ["Autonomie", "Scalabilité", "Isolation"],
            },
            {
                "title": "Patterns de Résilience et Cohérence",
                "bullets": ["Pattern Saga", "Circuit Breaker"],
            },
        ]

        report = validator.validate_course_and_slides_alignment(blueprint, slides_data)
        assert report.is_valid is True
        assert report.score == 1.0

    def test_remediate_with_bounded_retry_at_most_once(self, sample_course):
        validator = PedagogicalConsistencyValidator()
        blueprint = PedagogicalBlueprintService().derive_from_course(sample_course)

        call_count = 0

        def faulty_generator():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "Texte inadapté sans concept pertinent."
            return (
                "Synthèse corrigée : Les microservices et le pattern saga garantissent la résilience "
                "des architectures conteneurisées."
            )

        def check_alignment(text):
            return validator.validate_course_and_summary_alignment(blueprint, text)

        result, report = validator.remediate_with_bounded_retry(
            generator_fn=faulty_generator,
            validator_fn=check_alignment,
            max_retries=1,
        )

        assert call_count == 2
        assert report.is_valid is True
        assert "microservices" in result.lower()
