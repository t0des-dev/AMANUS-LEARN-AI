import json
import logging

from apps.ai.services import InsufficientContextError, Retriever, get_ai_provider
from apps.ai.services.context_builder import ContextBuilder
from apps.documents.models import Document
from apps.ingestion.models import DocumentChunk
from apps.quizzes.models import Quiz, QuizAnswer, QuizQuestion

from .validator import InvalidQuizQuestionError, QuizQuestionValidator

logger = logging.getLogger(__name__)


class QuizGeneratorService:
    """Generates RAG-grounded multiple-choice questions (QCM) from analyzed documents.

    Strict rule: Never insert unvalidated questions. LLM outputs are rigorously
    checked by QuizQuestionValidator before database persistence.
    """

    PROMPT_VERSION = "qcm-v1.0"

    SYSTEM_INSTRUCTION = (
        "Vous êtes un concepteur pédagogique expert spécialisé dans l'évaluation formative et sommative (QCM / Quiz). "
        "Votre rôle est d'analyser des extraits documentaires et de formuler des questions à choix multiples "
        "rigoureuses, fidèles aux sources et sans aucune hallucination.\n\n"
        "RÈGLES STRICTES D'ÉVALUATION :\n"
        "1. Chaque question doit comporter STRICTEMENT 4 options de réponse distinctes et plausibles.\n"
        "2. Exactement UNE SEULE option doit être correcte (les 3 autres sont des distracteurs erronés).\n"
        "3. Fournissez une explication claire justifiant la bonne réponse et citant la source [x].\n"
        "4. Indiquez la difficulté ('EASY', 'MEDIUM', 'HARD') et la source documentaire.\n"
        "5. Renvoyez OBLIGATOIREMENT un JSON structuré valide selon le format demandé."
    )

    def __init__(
        self,
        validator: QuizQuestionValidator | None = None,
        retriever: Retriever | None = None,
        context_builder: ContextBuilder | None = None,
    ):
        self.validator = validator or QuizQuestionValidator()
        self.retriever = retriever or Retriever()
        self.context_builder = context_builder or ContextBuilder()

    def generate_questions_for_quiz(
        self,
        quiz: Quiz,
        document: Document,
        provider_name: str | None = None,
        model: str | None = None,
        count: int = 5,
        focus: str | None = None,
        top_k: int = 8,
    ) -> list[QuizQuestion]:
        """Generates, validates, and persists QCM questions for a given Quiz."""
        # 1. RAG Source Retrieval & Safeguard Check
        chunk_count = DocumentChunk.objects.filter(document=document).count()
        if chunk_count == 0:
            raise InsufficientContextError(
                f"Le document « {document.title} » ne contient aucun chunk analysé. "
                "Veuillez traiter le document avant de générer un QCM."
            )

        query = (
            focus.strip()
            if focus and focus.strip()
            else f"{quiz.title} notions clés questions QCM examen"
        )

        ranked_sources = self.retriever.search_sources(
            query=query,
            organization_id=str(quiz.organization_id),
            document_id=str(document.id),
            top_k=top_k,
        )

        if not ranked_sources:
            # Fallback to direct chunks
            chunks = (
                DocumentChunk.objects.filter(document=document)
                .select_related("document", "page")
                .order_by("chunk_index")[:top_k]
            )
            ranked_sources = [
                {
                    "chunk_id": str(c.id),
                    "document_id": str(c.document_id),
                    "document_title": c.document.title,
                    "page": c.page.page_number if c.page else None,
                    "chapter": (
                        c.metadata.get("chapter") if isinstance(c.metadata, dict) else None
                    ),
                    "section": (
                        c.metadata.get("section") if isinstance(c.metadata, dict) else None
                    ),
                    "content": c.content,
                    "score": 1.0,
                    "metadata": c.metadata,
                }
                for c in chunks
            ]

        valid_sources = [s for s in ranked_sources if s.get("content", "").strip()]
        if not valid_sources:
            raise InsufficientContextError(
                f"Contexte insuffisant dans le document « {document.title} » pour générer un QCM."
            )

        context_text = self.context_builder.build_context(valid_sources)

        # 2. Build User Prompt
        user_prompt = (
            f"DOCUMENT SOURCE : « {document.title} »\n\n"
            f"EXTRAITS DOCUMENTAIRES RÉFÉRENCÉS :\n{context_text}\n\n"
            f"MISSION : Générer {count} questions à choix multiples (QCM) de niveau {quiz.difficulty} "
            f"pour le mode {quiz.get_type_display()}.\n\n"
            "FORMAT JSON OBLIGATOIRE :\n"
            "{\n"
            '  "questions": [\n'
            "    {\n"
            '      "question": "Énoncé précis et contextualisé ?",\n'
            '      "answers": [\n'
            '        {"text": "Bonne réponse exacte", "is_correct": true},\n'
            '        {"text": "Distracteur 1", "is_correct": false},\n'
            '        {"text": "Distracteur 2", "is_correct": false},\n'
            '        {"text": "Distracteur 3", "is_correct": false}\n'
            "      ],\n"
            '      "explanation": "Explication didactique sourcée [x]",\n'
            f'      "difficulty": "{quiz.difficulty}",\n'
            '      "source": "Titre du chapitre / section"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        # 3. Call AI Provider
        provider = get_ai_provider(provider_name)
        ai_response = provider.generate(
            prompt=user_prompt,
            system_instruction=self.SYSTEM_INSTRUCTION,
            model=model,
            response_format="json",
        )

        raw_data = ai_response.parsed_json
        if not raw_data:
            try:
                raw_data = json.loads(ai_response.content)
            except Exception as parse_err:
                raise InvalidQuizQuestionError(
                    f"Le modèle IA a renvoyé un contenu JSON invalide : {parse_err}"
                )

        # 4. Strict Validation of AI output before persistence
        validated_list = self.validator.validate_quiz_payload(
            raw_data, default_difficulty=quiz.difficulty
        )

        # 5. Persist into Database
        created_questions: list[QuizQuestion] = []
        current_order = quiz.questions.count()

        for q_data in validated_list:
            question_obj = QuizQuestion.objects.create(
                quiz=quiz,
                text=q_data["text"],
                explanation=q_data["explanation"],
                difficulty=q_data["difficulty"],
                source=q_data["source"],
                order=current_order,
            )
            current_order += 1

            for ans_data in q_data["answers"]:
                QuizAnswer.objects.create(
                    question=question_obj,
                    text=ans_data["text"],
                    is_correct=ans_data["is_correct"],
                    order=ans_data["order"],
                )

            created_questions.append(question_obj)

        logger.info(
            "Successfully created %s validated QCM questions for Quiz %s",
            len(created_questions),
            quiz.id,
        )
        return created_questions
