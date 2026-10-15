import json
from typing import Any

from .base import AIProvider, AIResponse
from .mock_fixtures import fixture as _fixture
from .mock_fixtures import fixture_text as _fixture_text


class MockAIProvider(AIProvider):
    """Deterministic Mock AI Provider for testing and offline development."""

    name: str = "mock"
    default_model: str = "mock-gpt-4o"

    def __init__(self, model_name: str = "mock-gpt-4o"):
        self.default_model = model_name

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 3000,
        response_format: str = "text",
    ) -> AIResponse:
        active_model = model or self.default_model
        input_tokens = max(1, len(prompt.split()) + len(system_instruction.split()))

        # If JSON is expected
        if response_format == "json":
            # Detect type from prompt
            lower_p = prompt.lower()
            if (
                '"slides":' in prompt
                or "diapositives" in lower_p
                or "diaporama" in lower_p
                or "شريحة" in prompt
                or "شرائح" in prompt
            ):
                if any(ar_term in prompt for ar_term in ["شرائح", "شريحة"]):
                    data = _fixture("slides_ar")
                elif (
                    "available sources" in lower_p
                    or "slide deck" in lower_p
                    or "presentation slides" in lower_p
                    or "language: en" in lower_p
                ):
                    data = _fixture("slides_en")
                else:
                    data = _fixture("slides_fr")
            elif (
                "qcm" in lower_p
                or "quiz" in lower_p
                or '"questions":' in prompt
                or "اختبار" in prompt
                or "أسئلة" in prompt
            ):
                adapted_q = self._generate_adapted_questions_from_prompt(prompt, lower_p)
                if adapted_q:
                    data = adapted_q
                elif any(
                    ar_term in prompt
                    for ar_term in [
                        "اللغة العربية",
                        "العربية",
                        "اختبار",
                        "أسئلة",
                        "سؤال",
                        "اختر الإجابة",
                    ]
                ):
                    data = _fixture('quiz_ar')
                elif "english" in lower_p or "in english" in lower_p or "language: en" in lower_p:
                    data = _fixture('quiz_en')
                else:
                    data = _fixture('quiz_fr')
            elif (
                "definitions" in prompt
                or "fiche de révision" in lower_p
                or "بطاقة مراجعة" in prompt
            ):
                data = _fixture('flashcard')
            elif (
                '"chapters":' in prompt
                or "un cours d'apprentissage" in lower_p
                or "educational course" in lower_p
                or "مقرر تعليمي" in prompt
                or ("cours" in lower_p and "résumé" not in lower_p and "overview" not in prompt)
            ):
                adapted = self._generate_adapted_course_from_prompt(prompt, lower_p)
                if adapted:
                    data = adapted
                elif any(
                    ar_term in prompt for ar_term in ["المستند", "مقرر", "دورة", "الفصل", "العربية"]
                ):
                    data = _fixture('course_ar')
                elif "en" in lower_p or "english" in lower_p:
                    data = _fixture('course_en')
                else:
                    data = _fixture('course_fr')
            elif (
                "key_points" in prompt
                or "concepts clés" in lower_p
                or "المفاهيم والنقاط الجوهرية" in prompt
            ):
                data = _fixture('key_points')
            elif (
                (
                    '"objectives":' in prompt
                    or "objectifs pédagogiques" in lower_p
                    or "الأهداف التعليمية" in prompt
                )
                and "chapters" not in prompt
                and "learning_objectives" not in prompt
            ):
                data = _fixture('objectives')
            elif (
                "overview" in prompt
                or "résumé" in lower_p
                or "resume" in lower_p
                or "summary" in lower_p
                or "ملخص" in prompt
            ):
                data: dict[str, Any] = _fixture('overview')
            elif (
                "podcast" in lower_p
                or "dialogue" in lower_p
                or "notebooklm" in lower_p
                or "بودكاست" in prompt
            ):
                data = _fixture('podcast')
            else:
                data = _fixture('fallback')

            content = json.dumps(data, ensure_ascii=False, indent=2)
            parsed_json = data
        else:
            # Plain text generation with pedagogical adaptations
            lower_all = (prompt + " " + system_instruction).lower()
            if "simplifi" in lower_all or "vulgaris" in lower_all:
                content = _fixture_text('simplified')
            elif "résum" in lower_all or "resum" in lower_all:
                content = _fixture_text('summary')
            elif "exemple" in lower_all or "illustr" in lower_all:
                content = _fixture_text('example')
            elif "interrog" in lower_all or "question" in lower_all or "quiz" in lower_all:
                content = _fixture_text('quiz_questions')
            elif "révis" in lower_all or "revis" in lower_all:
                content = _fixture_text('revision')
            elif "compar" in lower_all:
                content = _fixture_text('comparison')
            elif "défin" in lower_all or "defin" in lower_all:
                content = _fixture_text('definition')
            else:
                content = _fixture_text('default')
            parsed_json = None

        output_tokens = max(1, len(content.split()))

        return AIResponse(
            content=content,
            parsed_json=parsed_json,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=active_model,
            provider=self.name,
        )

    def _generate_adapted_course_from_prompt(
        self, prompt: str, lower_p: str
    ) -> dict[str, Any] | None:
        import re

        is_arabic = (
            any("\u0600" <= c <= "\u06FF" for c in prompt[:1000])
            or "العربية" in prompt
            or "المستند" in prompt
            or "الفصل" in prompt
        )
        is_english = ("en" in lower_p or "english" in lower_p) and not is_arabic

        # 1. Extract document title
        doc_title = ""
        for pat in [
            r'(?:المستند|DOCUMENT|Document)\s*:\s*«([^»]+)»',
            r'(?:المستند|DOCUMENT|Document)\s*:\s*"([^"]+)"',
            r'(?:المستند|DOCUMENT|Document)\s*:\s*[«"\'“](.*?)[»"\'”]',
        ]:
            m = re.search(pat, prompt)
            if m:
                doc_title = m.group(1).strip()
                break
        if not doc_title:
            title_match2 = re.search(r'(?:المستند|DOCUMENT|Document)\s*:\s*([^\n\r]+)', prompt)
            if title_match2:
                candidate = title_match2.group(1).strip().strip('«»"\'“').strip()
                if not any(token in candidate for token in ["NIVEAU", "CRITICAL", "MANDATORY"]):
                    doc_title = candidate

        # 2. Extract context / chunks from prompt
        context_text = ""
        for marker in [
            "المصادر والفقرات المتاحة :",
            "المصادر والفقرات المتاحة:",
            "SOURCES / EXTRAITS DU DOCUMENT :",
            "SOURCES / RETRIEVED CHUNKS:",
            "CONTEXT :",
            "CONTEXT:",
        ]:
            if marker in prompt:
                parts = prompt.split(marker, 1)
                if len(parts) > 1:
                    sub = parts[1]
                    for end_marker in [
                        "توجيه المستوى",
                        "NIVEAU CIBLE",
                        "FOCUS PARTICULIER",
                        "هيكل JSON",
                        "CRITICAL INSTRUCTIONS",
                        "MANDATORY JSON STRUCTURE",
                        "Structure JSON attendue",
                        "JSON structure",
                    ]:
                        if end_marker in sub:
                            sub = sub.split(end_marker, 1)[0]
                    context_text = sub.strip()
                    break

        # 3. Extract chunk blocks
        extracted_chunks = []
        if context_text:
            raw_chunks = re.split(r'(?:^|\n)---\s*Source\s*\[\d+\][^\n]*---\n?|\[\d+\]', context_text)
            for ch in raw_chunks:
                # Remove header lines like '--- Source [1] : ... ---'
                cleaned = re.sub(r'^[^\n]*---\n?', '', ch).strip()
                cleaned = re.sub(
                    r'^(?:Extrait|Source|Page|Document)[^\n:]*:', '', cleaned, flags=re.IGNORECASE
                ).strip()
                cleaned = re.sub(r'^[:\-—\s]+', '', cleaned).strip()
                if (
                    len(cleaned) > 25
                    and not cleaned.startswith("{")
                    and '"title":' not in cleaned
                    and "{" not in cleaned[:10]
                ):
                    extracted_chunks.append(cleaned)

        # If neither real title nor chunks were found (e.g. unit test using dummy query), return None for fallback
        if not doc_title and not extracted_chunks:
            return None

        # If chunks are empty but doc_title exists, create thematic chunks adapted to doc_title
        if not extracted_chunks and doc_title:
            extracted_chunks = [
                f"{doc_title} - الإطار العام والمفاهيم التأسيسية",
                f"{doc_title} - القواعد والأحكام الجوهرية المنظمة",
                f"{doc_title} - الإجراءات والآليات الميدانية والضمانات",
                f"{doc_title} - المعايير التطبيقية والأحكام الختامية",
            ] if is_arabic else [
                f"{doc_title} - Foundational Framework & Key Concepts",
                f"{doc_title} - Core Principles & Structural Guidelines",
                f"{doc_title} - Implementation Procedures & Safeguards",
                f"{doc_title} - Synthesis & Operational Standards",
            ] if is_english else [
                f"{doc_title} - Cadre Général & Notions Fondamentales",
                f"{doc_title} - Principes Directeurs & Règles Essentielles",
                f"{doc_title} - Modalités Pratiques & Garanties d'Application",
                f"{doc_title} - Synthèse Globale & Dispositions Clés",
            ]

        # Helper to extract a concise topic from chunk
        def _get_chunk_topic(text: str, default: str) -> str:
            lines = [line_item.strip() for line_item in text.split("\n") if line_item.strip()]
            for line in lines[:4]:
                clean_line = re.sub(r'^[#*_\-\s\d.:|]+', '', line).strip()
                clean_line = re.sub(r'--+.*--+', '', clean_line).strip()
                clean_line = re.sub(
                    r'^(?:Source|Extrait|Chapitre|Section)[^:]*:', '', clean_line, flags=re.IGNORECASE
                ).strip()
                words = clean_line.split()
                if 2 <= len(words) <= 12 and not clean_line.startswith("http"):
                    return clean_line
            return default

        # If chunks exist, partition into 3 to 6 chapters with lessons each
        if extracted_chunks:
            # If document has few chunks, ensure at least 3 distinct modules
            if len(extracted_chunks) < 3:
                base_c = extracted_chunks[0]
                while len(extracted_chunks) < 3:
                    extracted_chunks.append(base_c)

            total_chunks = len(extracted_chunks)
            num_chapters = min(6, max(3, (total_chunks + 1) // 2))
            chunks_per_chap = max(1, (total_chunks + num_chapters - 1) // num_chapters)

            chapters = []
            for ch_i in range(num_chapters):
                start_idx = ch_i * chunks_per_chap
                end_idx = min(total_chunks, start_idx + chunks_per_chap)
                ch_chunks = extracted_chunks[start_idx:end_idx]
                if not ch_chunks:
                    ch_chunks = [extracted_chunks[ch_i % len(extracted_chunks)]]

                lead_text = ch_chunks[0]
                if is_arabic:
                    thematic_suffixes = [
                        "الأسس النظرية والتأسيسية",
                        "المبادئ الجوهرية والتحليل المعمق",
                        "التطبيقات الميدانية ودراسات الحالة",
                        "المنهجيات وقواعد الاستيعاب",
                        "الخلاصة والتقييم الشامل",
                    ]
                    suffix = thematic_suffixes[ch_i % len(thematic_suffixes)]
                    ch_topic = _get_chunk_topic(lead_text, suffix)
                    ch_title = f"الفصل {ch_i + 1} : {ch_topic}"
                    ch_summary = f"دراسة تفصيلية وشاملة للمفاهيم المرتبطة بـ {ch_topic}."
                elif is_english:
                    thematic_suffixes = [
                        "Theoretical Foundations & Concepts",
                        "Core Principles & In-depth Analysis",
                        "Practical Applications & Case Studies",
                        "Methodology & Best Practices",
                        "Synthesis & Comprehensive Evaluation",
                    ]
                    suffix = thematic_suffixes[ch_i % len(thematic_suffixes)]
                    ch_topic = _get_chunk_topic(lead_text, suffix)
                    ch_title = f"Chapter {ch_i + 1}: {ch_topic}"
                    ch_summary = f"In-depth analysis of foundational concepts around {ch_topic}."
                else:
                    thematic_suffixes = [
                        "Fondements Théoriques & Notions Clés",
                        "Principes Directeurs & Analyse Approfondie",
                        "Applications Pratiques & Cas Réels",
                        "Méthodologie & Bonnes Pratiques",
                        "Synthèse Globale & Évaluation",
                    ]
                    suffix = thematic_suffixes[ch_i % len(thematic_suffixes)]
                    ch_topic = _get_chunk_topic(lead_text, suffix)
                    ch_title = f"Chapitre {ch_i + 1} : {ch_topic}"
                    ch_summary = f"Étude approfondie et structurée des concepts de {ch_topic}."

                sections = []
                for s_i, chunk_content in enumerate(ch_chunks):
                    if is_arabic:
                        s_default = f"المفهوم الرئيسي {s_i + 1}"
                        s_topic = _get_chunk_topic(chunk_content, s_default)
                        s_title = f"الدرس {ch_i + 1}.{s_i + 1} : {s_topic}"
                        content_md = (
                            f"## {s_topic}\n\n"
                            f"{chunk_content}\n\n"
                            f"### النقاط الرئيسية المستخلصة\n"
                            f"- تحليل وتأطير المفاهيم وفق الوثيقة المرجعية [1].\n"
                            f"- معايير التطبيق والمنهجية الميدانية [2].\n\n"
                            f"> **ملاحظة منهجية :** يجب التركيز على القواعد المعرفية المحددة في هذا الدرس لضمان الاستيعاب الدقيق."
                        )
                        s_obj = [f"استيعاب مبادئ {s_topic}"]
                        s_sum = (
                            chunk_content[:150] + "..."
                            if len(chunk_content) > 150
                            else chunk_content
                        )
                    elif is_english:
                        s_default = f"Core Concept {s_i + 1}"
                        s_topic = _get_chunk_topic(chunk_content, s_default)
                        s_title = f"Lesson {ch_i + 1}.{s_i + 1}: {s_topic}"
                        content_md = (
                            f"## {s_topic}\n\n"
                            f"{chunk_content}\n\n"
                            f"### Key Learning Takeaways\n"
                            f"- Core insights grounded directly in document source material [1].\n"
                            f"- Practical evaluation and application methodologies [2].\n\n"
                            f"> **Key Note:** Thorough understanding of this concept is essential for overall mastery."
                        )
                        s_obj = [f"Master the foundations of {s_topic}"]
                        s_sum = (
                            chunk_content[:150] + "..."
                            if len(chunk_content) > 150
                            else chunk_content
                        )
                    else:
                        s_default = f"Concept Clé {s_i + 1}"
                        s_topic = _get_chunk_topic(chunk_content, s_default)
                        s_title = f"Leçon {ch_i + 1}.{s_i + 1} : {s_topic}"
                        content_md = (
                            f"## {s_topic}\n\n"
                            f"{chunk_content}\n\n"
                            f"### Points Clés Pédagogiques\n"
                            f"- Analyse détaillée des notions extraites du document source [1].\n"
                            f"- Mise en perspective méthodologique et applications [2].\n\n"
                            f"> **Règle fondamentale :** Assimiler précisément les définitions et éléments structurels de ce module."
                        )
                        s_obj = [f"Comprendre et maîtriser les notions de {s_topic}"]
                        s_sum = (
                            chunk_content[:150] + "..."
                            if len(chunk_content) > 150
                            else chunk_content
                        )

                    sections.append(
                        {
                            "title": s_title,
                            "content": content_md,
                            "summary": s_sum,
                            "objectives": s_obj,
                            "estimated_minutes": 15 + (s_i * 5),
                        }
                    )

                chapters.append(
                    {
                        "title": ch_title,
                        "summary": ch_summary,
                        "estimated_minutes": 30 + (len(sections) * 10),
                        "sections": sections,
                    }
                )

            effective_title = (
                doc_title
                or (
                    "مقرر تعليمي شامل"
                    if is_arabic
                    else "Comprehensive Course" if is_english else "Cours Pédagogique Complet"
                )
            )
            if is_arabic:
                return {
                    "title": (
                        f"مقرر شامل : {effective_title}"
                        if not effective_title.startswith("مقرر")
                        else effective_title
                    ),
                    "description": f"دورة تعليمية شاملة مستخرجة بدقة من محتوى الوثيقة « {effective_title} »، تغطي كافة المحاور والنقاط الجوهرية.",
                    "level": "BEGINNER",
                    "learning_objectives": [
                        f"استيعاب المفاهيم والمحاور الأساسية لموضوع {effective_title}",
                        "التمكن من المنهجيات والآليات التطبيقية المستخلصة",
                        "تقييم المعارف المكتسبة وتطبيقها بدقة وفق الوثائق المرجعية",
                    ],
                    "chapters": chapters,
                    "conclusion": f"خاتمة شاملة وتقييم نهائي لمكتسبات دورة {effective_title}.",
                }
            elif is_english:
                return {
                    "title": f"Comprehensive Course: {effective_title}",
                    "description": f"Complete curriculum grounded faithfully in source material from '{effective_title}'.",
                    "level": "BEGINNER",
                    "learning_objectives": [
                        f"Understand the core concepts of {effective_title}",
                        "Analyze primary methodologies and practical frameworks",
                        "Demonstrate comprehensive mastery of source content",
                    ],
                    "chapters": chapters,
                    "conclusion": f"Comprehensive conclusion and final review of {effective_title}.",
                }
            else:
                return {
                    "title": (
                        f"Cours Complet : {effective_title}"
                        if not effective_title.startswith("Cours")
                        else effective_title
                    ),
                    "description": f"Programme pédagogique complet élaboré à partir du document « {effective_title} ».",
                    "level": "BEGINNER",
                    "learning_objectives": [
                        f"Maîtriser les concepts fondamentaux de {effective_title}",
                        "Analyser les méthodologies et démarches clés",
                        "Appliquer les connaissances issues du document source avec rigueur",
                    ],
                    "chapters": chapters,
                    "conclusion": f"Bilan global des acquis pédagogiques du cours {effective_title}.",
                }

        return None

    def _generate_adapted_questions_from_prompt(
        self, prompt: str, lower_p: str
    ) -> dict[str, Any] | None:
        """Dynamically generates grounded QCM questions based on actual document chunks and title in prompt."""
        import re

        # Detect language
        is_arabic = (
            any(
                ar_term in prompt
                for ar_term in [
                    "اللغة العربية",
                    "المستند المصدر",
                    "المقاطع المستندية",
                    "اختبار",
                    "أسئلة",
                    "سؤال",
                ]
            )
            or any("\u0600" <= c <= "\u06ff" for c in prompt[:300])
        )
        is_english = (
            "source document" in lower_p
            or "in english" in lower_p
            or ("generate" in lower_p and "questions" in lower_p and not is_arabic and "français" not in lower_p)
        )

        # 1. Extract document title
        doc_title = None
        for pattern in [
            r'المستند\s*المصدر\s*:\s*«([^»]+)»',
            r'المستند\s*:\s*«([^»]+)»',
            r'SOURCE DOCUMENT:\s*«([^»]+)»',
            r'DOCUMENT SOURCE\s*:\s*«([^»]+)»',
            r'DOCUMENT\s*:\s*«([^»]+)»',
            r'المستند\s*المصدر\s*:\s*"([^"]+)"',
            r'SOURCE DOCUMENT:\s*"([^"]+)"',
            r'DOCUMENT SOURCE\s*:\s*"([^"]+)"',
            r'DOCUMENT\s*:\s*"([^"]+)"',
        ]:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                doc_title = match.group(1).strip()
                break

        # 2. Extract textual chunks from prompt
        raw_chunks = re.split(
            r'\[(?:Extrait|المقطع|Chunk|Source)\s*\d+[^\]]*\]', prompt, flags=re.IGNORECASE
        )
        extracted_chunks: list[str] = []
        for c in raw_chunks:
            cleaned = c.strip()
            if (
                len(cleaned) > 40
                and not cleaned.startswith("JSON")
                and not cleaned.startswith("FORMAT")
                and not cleaned.startswith("MANDATORY")
                and not cleaned.startswith("تنسيق")
                and not cleaned.startswith("RÈGLES")
                and not cleaned.startswith("MISSION")
                and not cleaned.startswith("المهمة")
            ):
                extracted_chunks.append(cleaned)

        if not doc_title and not extracted_chunks:
            return None

        effective_title = doc_title or (
            "الوثيقة المعتمدة"
            if is_arabic
            else ("Source Material" if is_english else "Document Source")
        )

        def _get_chunk_topic(text: str, default: str) -> str:
            lines = [line_item.strip() for line_item in text.split("\n") if line_item.strip()]
            for line in lines[:3]:
                clean_line = re.sub(r'^[#*_\-\s\d.:]+', '', line).strip()
                words = clean_line.split()
                if 2 <= len(words) <= 12 and not clean_line.startswith("http"):
                    return clean_line
            return default

        # Target count from prompt
        count_match = re.search(r'(?:générer|generate|إنشاء)\s+(\d+)\s+questions', prompt, re.IGNORECASE)
        target_count = int(count_match.group(1)) if count_match else 5
        target_count = max(2, min(10, target_count))

        if not extracted_chunks:
            extracted_chunks = [effective_title]

        # Rich multi-angle templates to guarantee zero redundancy
        fr_templates = [
            (
                "Quelle est la notion fondamentale mise en avant dans « {title} » concernant {topic} ?",
                "L'application rigoureuse des principes méthodologiques établis dans la source [{src}]",
                "Une simplification excessive omettant les conditions de validité requises",
                "Un contournement direct des étapes analytiques documentées dans le texte",
                "Une hypothèse purement intuitive sans validation empirique formelle",
                "Le document « {title} » détaille scrupuleusement la validité de ce principe dans l'extrait [{src}].",
            ),
            (
                "Quel objectif d'apprentissage prioritaire ressort de « {title} » au sujet de {topic} ?",
                "La maîtrise opérationnelle des critères énoncés en référence [{src}]",
                "La mémorisation superficielle sans compréhension des mécanismes sous-jacents",
                "La substitution des règles prescrites par des approximations informelles",
                "L'abandon des contrôles de cohérence au profit de la rapidité d'exécution",
                "L'extrait [{src}] de la source « {title} » insiste expressément sur la maîtrise de ces critères.",
            ),
            (
                "Quelle démarche méthodologique est préconisée par « {title} » pour aborder {topic} ?",
                "Une démarche structurée respectant fidèlement le cadre de l'extrait [{src}]",
                "Une approche aléatoire non reproductible dans des conditions normales",
                "L'application d'un protocole obsolète contredit par les résultats actuels",
                "Une généralisation hâtive à partir d'un échantillon non représentatif",
                "La démarche recommandée dans « {title} » repose sur le cadre formalisé dans l'extrait [{src}].",
            ),
            (
                "Quel élément de validation essentiel est requis dans « {title} » pour {topic} ?",
                "La conformité vérifiable avec les données probantes de la source [{src}]",
                "La simple acceptation tacite d'un consensus non documenté",
                "Une tolérance arbitraire d'erreurs systématiques dans le processus",
                "Une validation unilatérale sans contrôle croisé ni vérification",
                "D'après « {title} », seule la conformité vérifiable avec l'extrait [{src}] garantit la rigueur.",
            ),
            (
                "Quelle conclusion opérationnelle se dégage de « {title} » concernant {topic} ?",
                "L'obtention de résultats mesurables et conformes aux exigences du document [{src}]",
                "Une incertitude méthodologique permanente invalidant l'analyse",
                "L'incapacité structurelle à relier les observations empiriques à la théorie",
                "Un écart persistant entre les objectifs déclarés et les réalisations",
                "Les conclusions présentées dans « {title} » démontrent l'atteinte des exigences de l'extrait [{src}].",
            ),
        ]

        ar_templates = [
            (
                "ما هي القاعدة النظرية الجوهرية المعتمدة في الوثيقة « {title} » بخصوص {topic}؟",
                "التطبيق المنهجي المعتمد وفقاً لما ورد في المصدر الموثق [{src}]",
                "افتراض مناقض يتعارض مع المعطيات الصريحة للمستند",
                "إجراء فرعي غير معتمد ضمن الشروط الأساسية للنص",
                "تفسير تقديري يخرج عن السياق الدقيق للوثيقة",
                "تؤكد الوثيقة « {title} » بوضوح في المقطع المرجعي [{src}] على صحة هذا الطرح وأهميته المنهجية.",
            ),
            (
                "ما هو الهدف البيداغوجي الأساسي الذي تركز عليه وثيقة « {title} » في {topic}؟",
                "استيعاب المعايير الإجرائية وتطبيقها بصرامة وفق المرجع [{src}]",
                "الحفظ السطحي للمصطلحات دون إدراك للعلاقات السببية",
                "استبدال القواعد المحددة بتقديرات جزافية غير مدروسة",
                "تجاهل شروط الضبط المنهجي الواردة في الإطار المرجعي",
                "يبرز المقطع [{src}] من « {title} » ضرورة استيعاب المعايير وتطبيقها بدقة بالغة.",
            ),
            (
                "أي منهجية عملية تدعو وثيقة « {title} » لاتباعها في معالجة {topic}؟",
                "نهج منظم يلتزم بالمحددات التحليلية المذكورة في المقطع [{src}]",
                "أسلوب عشوائي يفتقر إلى ضوابط القياس والمتابعة الميدانية",
                "اعتماد نماذج قديمة تم تفنيد نتائجها في التحليلات الحديثة",
                "تعميم غير مبرر يخالف المعايير التوجيهية للنص",
                "توصي الوثيقة « {title} » باعتماد التحليل المنظم المبين في المقطع المرجعي [{src}].",
            ),
            (
                "ما هو المعيار الحاسم لتقييم النتائج في موضوع {topic} حسب « {title} »؟",
                "التوافق التام مع البيانات والأدلة المستخرجة من المصدر [{src}]",
                "القبول الضمني بافتراضات غير موثقة بالبيانات الرسمية",
                "التساهل مع التناقضات المنهجية دون تصحيح أو تدقيق",
                "اعتماد خلاصات أحادية الجانب دون مقارنة موضوعية",
                "تشترط وثيقة « {title} » التحقق الصارم والمطابقة التامة مع بيانات المصدر [{src}].",
            ),
            (
                "ما هي الخلاصة التطبيقية الرئيسية المستفادة من الوثيقة « {title} » حول {topic}؟",
                "تحقيق كفاءة قابلة للتحقق والقياس وفق متطلبات الوثيقة [{src}]",
                "استمرار الغموض الإجرائي مما يعيق الاستفادة العملية",
                "العجز عن الربط بين المبادئ النظرية والممارسة الواقعية",
                "وجود فجوة منهجية دائمة بين الأهداف المعلنة ومخرجات العمل",
                "تُبرهن النتائج المدرجة في « {title} » على بلوغ الكفاءة المحددة بالمقطع [{src}].",
            ),
        ]

        en_templates = [
            (
                "What is the core theoretical principle established in '{title}' regarding {topic}?",
                "The methodological framework validated in referenced source [{src}]",
                "An ungrounded assumption directly contradicted by the source text",
                "A secondary mechanism omitted from the formal requirements",
                "An arbitrary extrapolation lacking documented evidence",
                "The document '{title}' explicitly substantiates this conclusion in reference [{src}].",
            ),
            (
                "What primary instructional goal does '{title}' emphasize in {topic}?",
                "Thorough conceptual mastery guided by criteria in reference [{src}]",
                "Superficial memorization without structural comprehension",
                "Replacing verified guidelines with informal estimations",
                "Omitting consistency audits during procedural execution",
                "Excerpt [{src}] in '{title}' emphasizes structured comprehension over rote recall.",
            ),
            (
                "Which rigorous methodology is recommended by '{title}' for {topic}?",
                "A structured protocol strictly adhering to excerpt [{src}]",
                "A non-reproducible heuristic lacking systematic controls",
                "An obsolete standard refuted by documented conclusions",
                "Over-generalization based on insufficient reference data",
                "The methodology outlined in '{title}' relies strictly upon the framework in excerpt [{src}].",
            ),
            (
                "What essential validation criterion is highlighted in '{title}' concerning {topic}?",
                "Verifiable alignment with empirical evidence cited in [{src}]",
                "Passive acceptance of uncorroborated consensus",
                "Arbitrary tolerance for uncalibrated procedural discrepancies",
                "Unilateral sign-off without independent verification",
                "According to '{title}', empirical alignment with source [{src}] remains the mandatory standard.",
            ),
            (
                "What key practical takeaway emerges from '{title}' regarding {topic}?",
                "Achieving reproducible performance meeting the standards in [{src}]",
                "Residual methodological ambiguity preventing sound implementation",
                "Failure to align theoretical foundations with operational practice",
                "A persistent disconnect between targeted outcomes and real-world results",
                "The operational conclusions in '{title}' affirm the benchmarks set in reference [{src}].",
            ),
        ]

        templates = ar_templates if is_arabic else (en_templates if is_english else fr_templates)

        questions = []
        for idx in range(target_count):
            tpl = templates[idx % len(templates)]
            chunk_text = extracted_chunks[idx % len(extracted_chunks)]
            source_num = (idx % len(extracted_chunks)) + 1
            default_label = f"المحور {idx + 1}" if is_arabic else (f"Section {idx + 1}" if is_english else f"Partie {idx + 1}")
            topic = _get_chunk_topic(chunk_text, default_label)

            q_text = tpl[0].format(title=effective_title, topic=topic)
            ans_correct = tpl[1].format(src=source_num)
            ans_d1 = tpl[2]
            ans_d2 = tpl[3]
            ans_d3 = tpl[4]
            explanation = tpl[5].format(title=effective_title, src=source_num)

            source_label = (
                f"« {effective_title} » - المقطع {source_num}"
                if is_arabic
                else (f"'{effective_title}' - Section {source_num}" if is_english else f"« {effective_title} » - Extrait {source_num}")
            )

            questions.append({
                "question": q_text,
                "answers": [
                    {"text": ans_correct, "is_correct": True},
                    {"text": ans_d1, "is_correct": False},
                    {"text": ans_d2, "is_correct": False},
                    {"text": ans_d3, "is_correct": False},
                ],
                "explanation": explanation,
                "difficulty": "MEDIUM",
                "source": source_label,
            })

        return {"questions": questions}


