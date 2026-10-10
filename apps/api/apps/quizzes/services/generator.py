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

    PROMPT_VERSION = "qcm-v2.0"

    SYSTEM_INSTRUCTIONS = {
        "fr": (
            "Vous êtes un concepteur pédagogique expert spécialisé dans l'évaluation formative et sommative (QCM / Quiz). "
            "Votre rôle est d'analyser des extraits documentaires et de formuler des questions à choix multiples "
            "rigoureuses, fidèles aux sources et sans aucune hallucination.\n\n"
            "RÈGLES PÉDAGOGIQUES STRICTES :\n"
            "1. Chaque question doit comporter STRICTEMENT 4 options de réponse distinctes, plausibles et de longueur homogène.\n"
            "2. Exactement UNE SEULE option doit être correcte (les 3 autres sont des distracteurs erronés fondés sur des confusions conceptuelles).\n"
            "3. Privilégiez l'évaluation de la compréhension, de l'application et de l'analyse selon la taxonomie de Bloom plutôt que la mémorisation superficielle.\n"
            "4. Proscrivez les questions négatives ou à double négation, ainsi que les méta-distracteurs ('Toutes les réponses', 'Aucune des réponses').\n"
            "5. Fournissez une explication pédagogique détaillée justifiant pourquoi la bonne réponse est exacte et citant la source [x].\n"
            "6. Indiquez la difficulté ('EASY', 'MEDIUM', 'HARD') et la source documentaire exacte.\n"
            "7. Renvoyez OBLIGATOIREMENT un JSON structuré valide selon le format demandé."
        ),
        "ar": (
            "أنت مصمم تعليمي خبير متخصص في التقييم التكويني والختامي (أسئلة الاختيار من متعدد QCM / الاختبارات). "
            "مهمتك هي تحليل المقاطع المستندية وصياغة أسئلة دقيقة، متوافقة تماماً مع المصادر وبدون أي تخمين أو هلوسة.\n\n"
            "القواعد البيداغوجية الصارمة:\n"
            "1. يجب أن يحتوي كل سؤال على 4 خيارات إجابة واضحة ومقنعة ذات طول متناسق.\n"
            "2. إجابة واحدة فقط صحيحة تماماً (والخيارات الثلاثة الأخرى هي مشتتات ذكية قائمة على الأخطاء الشائعة).\n"
            "3. قم بتقييم الفهم، والتطبيق، والتحليل (تصنيف بلوم)، وتجنب الحفظ السطحي للكلمات.\n"
            "4. تجنب تماماً الصياغات المزدوجة النفي أو المشتتات المرجعية مثل 'كل ما سبق' أو 'لا شيء مما سبق'.\n"
            "5. قدّم شرحاً تعليمياً مفصلاً يوضح سبب صحة الإجابة مع الإحالة إلى المصدر [x].\n"
            "6. حدد مستوى الصعوبة ('EASY', 'MEDIUM', 'HARD') والمصدر بدقة.\n"
            "7. أرجع حصراً كائن JSON مهيكل وصحيح وفقاً للنموذج المطلوب."
        ),
        "en": (
            "You are an expert instructional designer specializing in formative and summative assessment (multiple-choice questions / quizzes). "
            "Your role is to analyze documentary excerpts and formulate rigorous, strictly grounded questions without hallucination.\n\n"
            "STRICT INSTRUCTIONAL RULES:\n"
            "1. Each question must have STRICTLY 4 distinct, plausible options of similar length.\n"
            "2. Exactly ONE option must be correct (the 3 others are plausible distractors addressing common misconceptions).\n"
            "3. Test comprehension, application, and reasoning rather than shallow recall (Bloom's Taxonomy).\n"
            "4. Strictly avoid negative formulations, double negatives, and meta-distractors ('All of the above', 'None of the above').\n"
            "5. Provide a clear pedagogical explanation justifying the correct answer with source reference [x].\n"
            "6. Specify difficulty ('EASY', 'MEDIUM', 'HARD') and the document source.\n"
            "7. Return strictly valid structured JSON."
        ),
    }

    def __init__(
        self,
        validator: QuizQuestionValidator | None = None,
        retriever: Retriever | None = None,
        context_builder: ContextBuilder | None = None,
    ):
        self.validator = validator or QuizQuestionValidator()
        self.retriever = retriever or Retriever()
        self.context_builder = context_builder or ContextBuilder()

    def detect_target_language(
        self,
        quiz: Quiz,
        document: Document,
        language: str | None = None,
    ) -> str:
        """Determines target language (fr, ar, en) based on explicit arg, quiz, course, or document."""
        if language and str(language).strip():
            lang_code = str(language).strip().lower()[:2]
            if lang_code in ("fr", "ar", "en"):
                return lang_code

        # Course language
        if quiz.course and getattr(quiz.course, "language", None):
            c_lang = str(quiz.course.language).strip().lower()[:2]
            if c_lang in ("fr", "ar", "en"):
                return c_lang

        # Document language / metadata
        doc_lang = getattr(document, "language", None) or getattr(
            document, "detected_language", None
        )
        if doc_lang:
            d_code = str(doc_lang).strip().lower()[:2]
            if d_code in ("fr", "ar", "en"):
                return d_code

        # Check Arabic in title
        if any(c for c in (quiz.title + " " + document.title) if "\u0600" <= c <= "\u06ff"):
            return "ar"

        return "fr"

    def generate_questions_for_quiz(
        self,
        quiz: Quiz,
        document: Document,
        provider_name: str | None = None,
        model: str | None = None,
        count: int = 5,
        focus: str | None = None,
        top_k: int = 8,
        language: str | None = None,
    ) -> list[QuizQuestion]:
        """Generates, validates, and persists QCM questions for a given Quiz."""
        # 1. RAG Source Retrieval & Safeguard Check
        chunk_count = DocumentChunk.objects.filter(document=document).count()
        if chunk_count == 0:
            raise InsufficientContextError(
                f"Le document « {document.title} » ne contient aucun chunk analysé. "
                "Veuillez traiter le document avant de générer un QCM."
            )

        target_lang = self.detect_target_language(quiz, document, language=language)
        system_instruction = self.SYSTEM_INSTRUCTIONS.get(
            target_lang, self.SYSTEM_INSTRUCTIONS["fr"]
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

        # 2. Build User Prompt depending on language
        if target_lang == "ar":
            user_prompt = (
                f"المستند المصدر : « {document.title} »\n\n"
                f"المقاطع المستندية المرجعية :\n{context_text}\n\n"
                f"المهمة : قم بإنشاء {count} أسئلة اختيار من متعدد (QCM) باللغة العربية بمستوى صعوبة {quiz.difficulty} "
                f"لوضع التقييم {quiz.get_type_display()}.\n\n"
                "تنسيق JSON الإلزامي :\n"
                "{\n"
                '  "questions": [\n'
                "    {\n"
                '      "question": "نص السؤال الدقيق والمرتبط بالسياق؟",\n'
                '      "answers": [\n'
                '        {"text": "الإجابة الصحيحة الدقيقة", "is_correct": true},\n'
                '        {"text": "مشتت أول خاطئ", "is_correct": false},\n'
                '        {"text": "مشتت ثان خاطئ", "is_correct": false},\n'
                '        {"text": "مشتت ثالث خاطئ", "is_correct": false}\n'
                "      ],\n"
                '      "explanation": "شرح تعليمي واضح يوضح سبب صحة الخيار مستنداً إلى [x]",\n'
                f'      "difficulty": "{quiz.difficulty}",\n'
                '      "source": "عنوان الفصل أو القسم المستند إليه"\n'
                "    }\n"
                "  ]\n"
                "}"
            )
        elif target_lang == "en":
            user_prompt = (
                f"SOURCE DOCUMENT: « {document.title} »\n\n"
                f"REFERENCED DOCUMENTARY EXCERPTS:\n{context_text}\n\n"
                f"MISSION: Generate {count} multiple-choice questions (QCM) in English at {quiz.difficulty} level "
                f"for {quiz.get_type_display()} mode.\n\n"
                "MANDATORY JSON FORMAT:\n"
                "{\n"
                '  "questions": [\n'
                "    {\n"
                '      "question": "Precise and contextualized question?",\n'
                '      "answers": [\n'
                '        {"text": "Exact correct answer", "is_correct": true},\n'
                '        {"text": "Plausible distractor 1", "is_correct": false},\n'
                '        {"text": "Plausible distractor 2", "is_correct": false},\n'
                '        {"text": "Plausible distractor 3", "is_correct": false}\n'
                "      ],\n"
                '      "explanation": "Didactic explanation citing source [x]",\n'
                f'      "difficulty": "{quiz.difficulty}",\n'
                '      "source": "Chapter / Section title"\n'
                "    }\n"
                "  ]\n"
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT SOURCE : « {document.title} »\n\n"
                f"EXTRAITS DOCUMENTAIRES RÉFÉRENCÉS :\n{context_text}\n\n"
                f"MISSION : Générer {count} questions à choix multiples (QCM) en français de niveau {quiz.difficulty} "
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

        # 3. Call AI Provider with Transient Retry
        provider = get_ai_provider(provider_name)
        raw_data = None
        last_error = None

        for attempt in range(2):
            try:
                ai_response = provider.generate(
                    prompt=user_prompt,
                    system_instruction=system_instruction,
                    model=model,
                    response_format="json",
                )
                raw_data = ai_response.parsed_json
                if not raw_data and ai_response.content:
                    raw_data = json.loads(ai_response.content)
                if raw_data:
                    break
            except Exception as exc:
                last_error = exc
                logger.warning("Quiz generation attempt %s failed: %s", attempt + 1, exc)

        if not raw_data:
            raise InvalidQuizQuestionError(
                f"Le modèle IA n'a pas renvoyé de contenu JSON exploitable : {last_error}"
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
            "Successfully created %s validated QCM questions for Quiz %s (language=%s)",
            len(created_questions),
            quiz.id,
            target_lang,
        )
        return created_questions
