"""Versioned, reproducible benchmark reference dataset for Amanus Learn AI Evaluation (Sprint 06).

Version: 1.0.0
Zero PII, zero confidential secrets.
Contains multilingual test cases across French (fr), Arabic (ar), and English (en).
Covers normal, complex, boundary, and adversarial edge cases for all 5 generation pipelines.
"""

from dataclasses import dataclass, field
from typing import Any

DATASET_VERSION = "1.0.0"


@dataclass
class BenchmarkCase:
    """A single evaluation benchmark case."""

    case_id: str
    generator_type: str  # course, slides, audio, quiz, orchestration
    language: str  # fr, ar, en
    level: str  # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    description: str
    input_payload: dict[str, Any]
    expected_properties: dict[str, Any]
    is_edge_case: bool = False
    is_adversarial: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


BENCHMARK_DATASET: list[BenchmarkCase] = [
    # =========================================================================
    # 1. COURSES & DOCUMENTS GENERATION BENCHMARKS
    # =========================================================================
    BenchmarkCase(
        case_id="course_fr_beginner_algo",
        generator_type="course",
        language="fr",
        level="BEGINNER",
        description="Cours d'initiation aux algorithmes et structures de données (Français débutant)",
        input_payload={
            "title": "Introduction aux Algorithmes",
            "document_content": (
                "Un algorithme est une suite ordonnée d'instructions permettant de résoudre un problème [1]. "
                "Les listes et dictionnaires constituent les structures fondamentales en Python [2]. "
                "La complexité temporelle s'exprime par la notation Grand O pour mesurer l'efficacité [3]."
            ),
            "target_language": "fr",
            "target_level": "BEGINNER",
        },
        expected_properties={
            "min_chapters": 1,
            "min_lessons_per_chapter": 2,
            "requires_citations": True,
            "forbidden_terms": ["null", "undefined"],
        },
    ),
    BenchmarkCase(
        case_id="course_ar_advanced_transformers",
        generator_type="course",
        language="ar",
        level="ADVANCED",
        description="مقرر متقدم في آليات الانتباه ونماذج المحولات (عربي متقدم)",
        input_payload={
            "title": "هندسة نماذج المحولات وآليات الانتباه",
            "document_content": (
                "تعتمد بنية المحولات (Transformer) على آلية الانتباه الذاتي المتعدد الرؤوس (Multi-Head Attention) [1]. "
                "تتيح هذه الآلية معالجة الرموز اللغوية بالتوازي دون الحاجة إلى شبكات التكرار الزمنية التقليدية [2]. "
                "تساهم طبقات التطبيع (Layer Normalization) والاتصالات المتبقية (Residual Connections) في استقرار التدريب [3]."
            ),
            "target_language": "ar",
            "target_level": "ADVANCED",
        },
        expected_properties={
            "min_chapters": 1,
            "min_lessons_per_chapter": 2,
            "requires_citations": True,
            "arabic_unicode_preservation": True,
        },
    ),
    BenchmarkCase(
        case_id="course_en_intermediate_microservices",
        generator_type="course",
        language="en",
        level="INTERMEDIATE",
        description="Intermediate course on microservices and distributed patterns (English)",
        input_payload={
            "title": "Cloud-Native Microservices Architecture",
            "document_content": (
                "Microservices isolate business capabilities into autonomous, independently deployable services [1]. "
                "Communication occurs asynchronously via event brokers or synchronously via REST/gRPC [2]. "
                "The Saga pattern coordinates distributed transactions without two-phase locking [3]."
            ),
            "target_language": "en",
            "target_level": "INTERMEDIATE",
        },
        expected_properties={
            "min_chapters": 1,
            "min_lessons_per_chapter": 2,
            "requires_citations": True,
        },
    ),
    BenchmarkCase(
        case_id="course_edge_empty_document",
        generator_type="course",
        language="fr",
        level="BEGINNER",
        description="Document vide ou sans chunks (garde-fou zéro hallucination)",
        input_payload={
            "title": "Document Vide",
            "document_content": "",
            "target_language": "fr",
            "target_level": "BEGINNER",
        },
        expected_properties={
            "expected_rejection": True,
            "expected_error": "InsufficientContextError",
        },
        is_edge_case=True,
    ),
    BenchmarkCase(
        case_id="course_edge_malformed_structure",
        generator_type="course",
        language="fr",
        level="BEGINNER",
        description="Payload généré malformé avec clés manquantes ou types invalides",
        input_payload={
            "raw_invalid_payload": {"title": 12345, "chapters": "not_a_list"},
        },
        expected_properties={
            "expected_rejection": True,
            "expected_error": "InvalidCoursePayloadError",
        },
        is_edge_case=True,
        is_adversarial=True,
    ),
    # =========================================================================
    # 2. SLIDES & PPTX PRESENTATIONS BENCHMARKS
    # =========================================================================
    BenchmarkCase(
        case_id="slides_fr_standard_5slides",
        generator_type="slides",
        language="fr",
        level="INTERMEDIATE",
        description="Présentation pédagogique standard de 5 diapositives (Français)",
        input_payload={
            "title": "Fondamentaux de l'Intelligence Artificielle",
            "slide_count": 5,
            "theme": "modern",
            "language": "fr",
        },
        expected_properties={
            "exact_slide_count": 5,
            "max_bullets_per_slide": 6,
            "max_chars_per_bullet": 160,
            "aspect_ratio": "16:9",
        },
    ),
    BenchmarkCase(
        case_id="slides_ar_rtl_presentation",
        generator_type="slides",
        language="ar",
        level="ADVANCED",
        description="عرض تقديمي تقني باللغة العربية مع دعم المحاذاة من اليمين إلى اليسار (RTL)",
        input_payload={
            "title": "مقدمة في التعلم العميق والشبكات العصبية",
            "slide_count": 4,
            "theme": "corporate",
            "language": "ar",
        },
        expected_properties={
            "exact_slide_count": 4,
            "rtl_support": True,
            "aspect_ratio": "16:9",
            "arabic_unicode_preservation": True,
        },
    ),
    BenchmarkCase(
        case_id="slides_edge_overflow_density",
        generator_type="slides",
        language="fr",
        level="EXPERT",
        description="Diapositive candidate surchargée de texte pour tester le détecteur de débordement",
        input_payload={
            "title": "Slide surchargée",
            "slide_content": "\n".join(
                [
                    f"Puce détaillée numéro {i} contenant une explication verbeuse qui dépasse la limite normale"
                    for i in range(12)
                ]
            ),
            "slide_number": 1,
        },
        expected_properties={
            "density_violation_expected": True,
            "max_allowed_bullets": 6,
        },
        is_edge_case=True,
    ),
    BenchmarkCase(
        case_id="slides_edge_empty_presentation",
        generator_type="slides",
        language="fr",
        level="BEGINNER",
        description="Présentation vide sans aucune diapositive (rejet à l'export PPTX)",
        input_payload={
            "title": "Deck vide",
            "slides": [],
        },
        expected_properties={
            "expected_rejection": True,
            "expected_error": "empty_presentation",
        },
        is_edge_case=True,
    ),
    # =========================================================================
    # 3. AUDIO & TTS SYNTHESIS BENCHMARKS
    # =========================================================================
    BenchmarkCase(
        case_id="audio_fr_pedagogical_lecture",
        generator_type="audio",
        language="fr",
        level="INTERMEDIATE",
        description="Script de cours oralisé en français avec ton pédagogique",
        input_payload={
            "text": (
                "Bienvenue dans cette leçon consacrée à la recherche binaire. "
                "La recherche binaire est un algorithme efficace qui divise par deux l'espace de recherche à chaque étape. "
                "Sa complexité temporelle est logarithmique en O de log n."
            ),
            "voice": "alloy",
            "language": "fr",
        },
        expected_properties={
            "valid_magic_header": True,
            "min_bytes": 48,
            "expected_wpm_range": (110, 180),
        },
    ),
    BenchmarkCase(
        case_id="audio_ar_unicode_script",
        generator_type="audio",
        language="ar",
        level="INTERMEDIATE",
        description="نص تعليمي صوتي باللغة العربية مع علامات ترقيم سليمة",
        input_payload={
            "text": (
                "مرحباً بكم في هذا الدرس الصوتي حول هياكل البيانات. "
                "تعتبر القوائم المترابطة عنصراً أساسياً في تخزين البيانات ديناميكياً؛ "
                "فهل تساءلتم يوماً كيف تُدار الذاكرة بكفاءة؟ سنكتشف ذلك معاً."
            ),
            "voice": "alloy",
            "language": "ar",
        },
        expected_properties={
            "valid_magic_header": True,
            "min_bytes": 48,
            "arabic_punctuation_handled": True,
        },
    ),
    BenchmarkCase(
        case_id="audio_long_multichunk_preservation",
        generator_type="audio",
        language="fr",
        level="ADVANCED",
        description="Texte éducatif long (> 2800 caractères) nécessitant un découpage multi-chunks sans perte de mot",
        input_payload={
            "text": "\n\n".join(
                [
                    f"Paragraphe pédagogique {i} : Dans ce paragraphe, nous analysons la méthode {i} de factorisation et de cryptographie moderne. "
                    f"Cette méthode garantit une sécurité optimale à condition de respecter les longueurs de clés prescrites."
                    for i in range(1, 15)
                ]
            ),
            "voice": "alloy",
            "language": "fr",
        },
        expected_properties={
            "requires_chunking": True,
            "zero_word_loss": True,
            "zero_word_duplication": True,
        },
    ),
    BenchmarkCase(
        case_id="audio_edge_empty_script",
        generator_type="audio",
        language="fr",
        level="BEGINNER",
        description="Script audio vide ou contenant uniquement des espaces",
        input_payload={"text": "   \n\t  "},
        expected_properties={
            "expected_rejection": True,
            "expected_chunks_count": 0,
        },
        is_edge_case=True,
    ),
    # =========================================================================
    # 4. QUIZZES & ASSESSMENTS BENCHMARKS
    # =========================================================================
    BenchmarkCase(
        case_id="quiz_fr_pedagogical_qcm",
        generator_type="quiz",
        language="fr",
        level="INTERMEDIATE",
        description="QCM pédagogique en français avec exactement 4 choix, 1 vraie et explication sourcée",
        input_payload={
            "question": "Quelle est la complexité temporelle moyenne d'une recherche dans une table de hachage bien dimensionnée ?",
            "answers": [
                {"text": "O(1) en temps constant", "is_correct": True},
                {"text": "O(n) en temps linéaire", "is_correct": False},
                {"text": "O(log n) en temps logarithmique", "is_correct": False},
                {"text": "O(n²) en temps quadratique", "is_correct": False},
            ],
            "explanation": "La fonction de hachage calcule directement l'adresse mémoire de l'élément recherché [1].",
            "difficulty": "MEDIUM",
            "source": "Chapitre 3 : Tables de hachage",
        },
        expected_properties={
            "exact_options_count": 4,
            "single_correct_answer": True,
            "non_empty_explanation": True,
            "absence_of_meta_distractor": True,
        },
    ),
    BenchmarkCase(
        case_id="quiz_ar_technical_qcm",
        generator_type="quiz",
        language="ar",
        level="ADVANCED",
        description="سؤال تقني باللغة العربية مع 4 خيارات وتبرير تربوي واضح",
        input_payload={
            "question": "ما هي الفائدة الأساسية من استخدام طبقات التسوية (Dropout) أثناء تدريب الشبكات العصبية العميقة؟",
            "answers": [
                {
                    "text": "الحد من فرط التخصيص (Overfitting) من خلال تعطيل خلايا عشوائياً",
                    "is_correct": True,
                },
                {"text": "زيادة عدد المعاملات القابلة للتدريب تلقائياً", "is_correct": False},
                {"text": "تسريع الحسابات الرياضية بإلغاء مصفوفات الأوزان", "is_correct": False},
                {"text": "ضمان دقة 100% على بيانات الاختبار بدون تدريب", "is_correct": False},
            ],
            "explanation": "تعمل تقنية Dropout على منع الاعتماد المتبادل المفرط بين الخلايا العصبية [2].",
            "difficulty": "HARD",
            "source": "الفصل 4 : تقنيات التعلم العميق",
        },
        expected_properties={
            "exact_options_count": 4,
            "single_correct_answer": True,
            "arabic_unicode_preservation": True,
        },
    ),
    BenchmarkCase(
        case_id="quiz_edge_banned_meta_distractor",
        generator_type="quiz",
        language="fr",
        level="BEGINNER",
        description="Question candidate contenant un distracteur méta interdit ('Toutes les réponses ci-dessus')",
        input_payload={
            "question": "Lesquelles de ces propriétés sont vraies ?",
            "answers": [
                {"text": "Propriété A", "is_correct": False},
                {"text": "Propriété B", "is_correct": False},
                {"text": "Propriété C", "is_correct": False},
                {"text": "Toutes les réponses ci-dessus sont vraies", "is_correct": True},
            ],
            "explanation": "Car toutes sont valides.",
            "difficulty": "EASY",
        },
        expected_properties={
            "expected_rejection": True,
            "expected_error": "meta_distractor_detected",
        },
        is_edge_case=True,
        is_adversarial=True,
    ),
    BenchmarkCase(
        case_id="quiz_edge_multiple_correct_answers",
        generator_type="quiz",
        language="fr",
        level="BEGINNER",
        description="Question candidate erronée contenant deux réponses marquées correctes",
        input_payload={
            "question": "Quelle est la capitale de la France ?",
            "answers": [
                {"text": "Paris", "is_correct": True},
                {"text": "Lyon", "is_correct": True},
                {"text": "Marseille", "is_correct": False},
                {"text": "Toulouse", "is_correct": False},
            ],
            "explanation": "Paris et Lyon sont de grandes villes.",
            "difficulty": "EASY",
        },
        expected_properties={
            "expected_rejection": True,
            "expected_error": "multiple_correct_answers",
        },
        is_edge_case=True,
        is_adversarial=True,
    ),
    # =========================================================================
    # 5. ORCHESTRATION & PIPELINE BENCHMARKS
    # =========================================================================
    BenchmarkCase(
        case_id="orchestration_standard_flow",
        generator_type="orchestration",
        language="fr",
        level="BEGINNER",
        description="Workflow complet d'orchestration : tracking, lock, mise en cache et calcul télémétrique",
        input_payload={
            "task_id": "eval-task-001",
            "organization_id": "org-eval-alpha",
            "resource_type": "course",
            "resource_id": "course-eval-123",
            "input_tokens": 1500,
            "output_tokens": 850,
            "model": "gpt-4o",
        },
        expected_properties={
            "valid_lifecycle_status": True,
            "isolated_to_org": "org-eval-alpha",
            "cost_calculated": True,
        },
    ),
    BenchmarkCase(
        case_id="orchestration_concurrency_conflict",
        generator_type="orchestration",
        language="fr",
        level="BEGINNER",
        description="Tentative d'exécution concurrente sur une ressource déjà verrouillée (rejet 409)",
        input_payload={
            "resource_type": "course",
            "resource_id": "locked-resource-999",
            "simulate_active_lock": True,
        },
        expected_properties={
            "conflict_409_expected": True,
        },
        is_edge_case=True,
    ),
]


def get_benchmark_cases_by_type(generator_type: str) -> list[BenchmarkCase]:
    """Retrieves benchmark test cases filtered by generator type."""
    target = generator_type.lower().strip()
    return [c for c in BENCHMARK_DATASET if c.generator_type.lower().strip() == target]
