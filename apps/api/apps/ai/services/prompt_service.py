class PromptService:
    """Manages prompt engineering, system instructions, and explicit prompt versioning.

    Supports multilingual generation in French (fr), Arabic (ar), and English (en),
    with pedagogical adaptation to the learner's level (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT).
    """

    VERSION = "v1.0"

    BASE_SYSTEM_INSTRUCTION = (
        "Vous êtes un assistant pédagogique IA expert pour la plateforme EdTech 'Amanus Learn AI'. "
        "Votre rôle est d'analyser des documents de cours ou de formation et de générer du contenu "
        "pédagogique structuré, clair, précis et rigoureusement fidèle au document fourni.\n\n"
        "RÈGLES ABSOLUES :\n"
        "1. Basez TOUTES vos affirmations STRICTEMENT et EXCLUSIVEMENT sur les sources documentaires transmises.\n"
        "2. N'inventez AUCUN fait, chiffre ou concept absent des sources (zéro hallucination).\n"
        "3. Incluez des citations de sources sous la forme [1], [2] dès que vous affirmez un fait précis.\n"
        "4. Si les sources sont insuffisantes pour traiter un aspect, indiquez-le explicitement.\n"
        "5. Renvoyez TOUJOURS un JSON valide et structuré selon le schéma attendu."
    )

    SYSTEM_INSTRUCTIONS_BY_LANG = {
        "fr": BASE_SYSTEM_INSTRUCTION,
        "en": (
            "You are an expert pedagogical AI assistant for the EdTech platform 'Amanus Learn AI'. "
            "Your role is to analyze course and training documents and generate structured, clear, "
            "accurate pedagogical content strictly grounded in the provided document.\n\n"
            "ABSOLUTE RULES:\n"
            "1. Base ALL statements STRICTLY and EXCLUSIVELY on the provided source documents.\n"
            "2. Invent NO facts, numbers, or concepts absent from the sources (zero hallucination).\n"
            "3. Include source citations like [1], [2] whenever stating a specific fact.\n"
            "4. If sources are insufficient to address a point, state it explicitly.\n"
            "5. ALWAYS return valid, structured JSON according to the requested schema."
        ),
        "ar": (
            "أنت مساعد تربوي ذكي وخبير في منصة 'Amanus Learn AI' للتعليم الذكي. "
            "مهمتك هي تحليل المستندات والمقررات وتوليد محتوى تعليمي منظم ودقيق ومطابق تماماً "
            "للوثائق المرفقة باللغة العربية الفصحى السليمة.\n\n"
            "القواعد الصارمة والأساسية:\n"
            "1. استند في جميع إجاباتك ومعلوماتك حصرياً وبشكل صارم على المصادر المرفقة.\n"
            "2. لا تخترع أي حقائق أو أرقام أو مفاهيم غير موجودة في المصادر (انعدام تام للهلوسة).\n"
            "3. أدرج إحالات وتوثيق المصادر بصيغة [1] أو [2] عند ذكر أي معلومة مستندة إلى نص المصدر.\n"
            "4. إذا كانت المصادر غير كافية، وضّح ذلك صراحة وبكل شفافية.\n"
            "5. أعد دائماً مخرجات بصيغة JSON صحيحة ومنظمة وفق الهيكل المطلوب بدقة."
        ),
    }

    LEVEL_DIRECTIVES = {
        "BEGINNER": {
            "fr": "Niveau DÉBUTANT : explications simples, analogies concrètes, vulgarisation progressive.",
            "en": "BEGINNER Level: simple explanations, intuitive analogies, step-by-step introduction.",
            "ar": "مستوى المبتدئين: شروحات مبسطة، أمثلة توضيحية، تدرج سلس في المفاهيم.",
        },
        "INTERMEDIATE": {
            "fr": "Niveau INTERMÉDIAIRE : équilibre théorie et cas pratiques, analyse méthodologique.",
            "en": "INTERMEDIATE Level: balanced theory and practice, solid methodological analysis.",
            "ar": "المستوى المتوسط: توازن بين النظريات والتطبيقات العملية والتحليل المنهجي.",
        },
        "ADVANCED": {
            "fr": "Niveau AVANCÉ : rigueur conceptuelle, cas d'usage approfondis, synthèse critique.",
            "en": "ADVANCED Level: conceptual rigor, in-depth specialized case studies, critical synthesis.",
            "ar": "المستوى المتقدم: عمق منهجي ومفاهيمي، دراسة حالات متقدمة، وتحليل نقدي.",
        },
        "EXPERT": {
            "fr": "Niveau EXPERT : analyse exhaustive, formalisation technique, perspectives professionnelles.",
            "en": "EXPERT Level: exhaustive technical formalization, high-level professional frameworks.",
            "ar": "مستوى الخبراء: تأطير تقني وعلمي دقيق، ومنهجيات احترافية شاملة.",
        },
    }

    def _get_system_instruction(self, language: str = "fr") -> str:
        lang = (language or "fr").lower()
        return self.SYSTEM_INSTRUCTIONS_BY_LANG.get(lang, self.BASE_SYSTEM_INSTRUCTION)

    def _get_level_directive(self, level: str = "BEGINNER", language: str = "fr") -> str:
        lvl = (level or "BEGINNER").upper()
        lang = (language or "fr").lower()
        lvl_dict = self.LEVEL_DIRECTIVES.get(lvl, self.LEVEL_DIRECTIVES["BEGINNER"])
        return lvl_dict.get(lang, lvl_dict["fr"])

    def get_summary_prompt(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
    ) -> tuple[str, str, str]:
        """Generates system, user prompt, and prompt version for document summary."""
        lang = (language or "fr").lower()
        system_instruction = self._get_system_instruction(lang)
        level_directive = self._get_level_directive(level, lang)
        focus_directive = f"\nFOCUS PARTICULIER : {focus}" if focus else ""

        if lang == "ar":
            user_prompt = (
                f"المستند المرجعي : « {document_title} »\n\n"
                f"المصادر والفقرات المتاحة :\n{context}\n\n"
                f"توجيه المستوى : {level_directive}{focus_directive}\n"
                "المهمة : إعداد ملخص شامل ومنظم وموثق باللغة العربية الفصحى لهذا المستند.\n"
                "هيكل JSON الإلزامي :\n"
                "{\n"
                '  "overview": "خلاصة عامة في فقرتين أو 3 فقرات مركزة",\n'
                '  "key_takeaways": ["نقطة جوهرية 1 مع الإحالة [x]", "نقطة جوهرية 2..."],\n'
                '  "chapters_summary": [\n'
                '    {"title": "عنوان الفصل أو المحور", "summary": "ملخص شامل للمحور"}\n'
                "  ]\n"
                "}"
            )
        elif lang == "en":
            user_prompt = (
                f'DOCUMENT: "{document_title}"\n\n'
                f"AVAILABLE SOURCES:\n{context}\n\n"
                f"LEVEL DIRECTIVE: {level_directive}{focus_directive}\n"
                "MISSION: Write a comprehensive, well-structured educational summary of this document.\n"
                "Mandatory JSON format:\n"
                "{\n"
                '  "overview": "Overall synthesis in 2-3 paragraphs",\n'
                '  "key_takeaways": ["Key point 1 with source [x]", "Key point 2..."],\n'
                '  "chapters_summary": [\n'
                '    {"title": "Chapter or section title", "summary": "Chapter summary"}\n'
                "  ]\n"
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
                f"DIRECTIVE DE NIVEAU : {level_directive}{focus_directive}\n"
                "MISSION : Rédiger un résumé exhaustif et structuré de ce document.\n"
                "Format JSON obligatoire :\n"
                "{\n"
                '  "overview": "Synthèse globale en 2-3 paragraphes",\n'
                '  "key_takeaways": ["Point clé 1 avec source [x]", "Point clé 2..."],\n'
                '  "chapters_summary": [\n'
                '    {"title": "Titre du chapitre ou partie", "summary": "Résumé du chapitre"}\n'
                "  ]\n"
                "}"
            )
        return system_instruction, user_prompt, f"summary-{self.VERSION}"

    def get_key_points_prompt(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
    ) -> tuple[str, str, str]:
        """Generates prompts for extracting essential key points and core concepts."""
        lang = (language or "fr").lower()
        system_instruction = self._get_system_instruction(lang)
        focus_directive = f"\nFOCUS PARTICULIER : {focus}" if focus else ""

        if lang == "ar":
            user_prompt = (
                f"المستند : « {document_title} »\n\n"
                f"المصادر المتاحة :\n{context}\n{focus_directive}\n"
                "المهمة : استخراج المفاهيم والنقاط الجوهرية الواجب استيعابها بدقة.\n"
                "هيكل JSON الإلزامي :\n"
                "{\n"
                '  "key_points": [\n'
                '    {"point": "اسم المفهوم أو القاعدة", "explanation": "شرح دقيق موثق بالإحالة [x]"}\n'
                "  ]\n"
                "}"
            )
        elif lang == "en":
            user_prompt = (
                f'DOCUMENT: "{document_title}"\n\n'
                f"AVAILABLE SOURCES:\n{context}\n{focus_directive}\n"
                "MISSION: Extract essential notions and key takeaways that must be retained.\n"
                "Mandatory JSON format:\n"
                "{\n"
                '  "key_points": [\n'
                '    {"point": "Notion or rule name", "explanation": "Detailed explanation with source [x]"}\n'
                "  ]\n"
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n{focus_directive}\n"
                "MISSION : Extraire les notions essentielles et points clés à retenir absolument.\n"
                "Format JSON obligatoire :\n"
                "{\n"
                '  "key_points": [\n'
                '    {"point": "Nom de la notion ou règle", "explanation": "Explication détaillée sourcée [x]"}\n'
                "  ]\n"
                "}"
            )
        return system_instruction, user_prompt, f"key-points-{self.VERSION}"

    def get_objectives_prompt(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
    ) -> tuple[str, str, str]:
        """Generates prompts for educational learning objectives."""
        lang = (language or "fr").lower()
        system_instruction = self._get_system_instruction(lang)
        focus_directive = f"\nFOCUS PARTICULIER : {focus}" if focus else ""

        if lang == "ar":
            user_prompt = (
                f"المستند : « {document_title} »\n\n"
                f"المصادر المتاحة :\n{context}\n{focus_directive}\n"
                "المهمة : صياغة الأهداف التعليمية الدقيقة وفق تصنيف بلوم (الفهم، التطبيق، التحليل، التقييم).\n"
                "هيكل JSON الإلزامي :\n"
                "{\n"
                '  "objectives": [\n'
                '    {"level": "الفهم / التطبيق / التحليل", "objective": "هدف تعليمي مصاغ بفعل إجرائي محدد"}\n'
                "  ]\n"
                "}"
            )
        elif lang == "en":
            user_prompt = (
                f'DOCUMENT: "{document_title}"\n\n'
                f"AVAILABLE SOURCES:\n{context}\n{focus_directive}\n"
                "MISSION: Formulate learning objectives according to educational taxonomies (Understand, Apply, Analyze, Evaluate).\n"
                "Mandatory JSON format:\n"
                "{\n"
                '  "objectives": [\n'
                '    {"level": "Understand / Apply / Analyze", "objective": "Objective formulated with an action verb"}\n'
                "  ]\n"
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n{focus_directive}\n"
                "MISSION : Définir les objectifs pédagogiques (selon la taxonomie d'apprentissage : Comprendre, Appliquer, Analyser, Évaluer).\n"
                "Format JSON obligatoire :\n"
                "{\n"
                '  "objectives": [\n'
                '    {"level": "Comprendre / Appliquer / etc.", "objective": "Objectif formulé avec verbe d\'action"}\n'
                "  ]\n"
                "}"
            )
        return system_instruction, user_prompt, f"objectives-{self.VERSION}"

    def get_revision_sheet_prompt(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
    ) -> tuple[str, str, str]:
        """Generates prompts for revision sheet (fiche de révision)."""
        lang = (language or "fr").lower()
        system_instruction = self._get_system_instruction(lang)
        focus_directive = f"\nFOCUS PARTICULIER : {focus}" if focus else ""

        if lang == "ar":
            user_prompt = (
                f"المستند : « {document_title} »\n\n"
                f"المصادر المتاحة :\n{context}\n{focus_directive}\n"
                "المهمة : إنشاء بطاقة مراجعة تعليمية مركزة وشاملة للاختبارات باللغة العربية.\n"
                "هيكل JSON الإلزامي :\n"
                "{\n"
                '  "title": "عنوان بطاقة المراجعة",\n'
                '  "definitions": [{"term": "المصطلح", "definition": "تعريف دقيق موثق بالمصدر [x]"}],\n'
                '  "key_formulas_or_rules": ["قاعدة 1", "قاعدة 2"],\n'
                '  "frequent_mistakes": ["فخ أو خطأ شائع يجب تفاديه"],\n'
                '  "quick_qa": [{"question": "سؤال تدريبي", "answer": "إجابة موجزة"}]\n'
                "}"
            )
        elif lang == "en":
            user_prompt = (
                f'DOCUMENT: "{document_title}"\n\n'
                f"AVAILABLE SOURCES:\n{context}\n{focus_directive}\n"
                "MISSION: Create a concise, structured exam revision sheet.\n"
                "Mandatory JSON format:\n"
                "{\n"
                '  "title": "Revision sheet title",\n'
                '  "definitions": [{"term": "Term", "definition": "Accurate definition cited [x]"}],\n'
                '  "key_formulas_or_rules": ["Rule or formula 1", "Rule 2"],\n'
                '  "frequent_mistakes": ["Classic pitfall to avoid"],\n'
                '  "quick_qa": [{"question": "Typical question", "answer": "Brief answer"}]\n'
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n{focus_directive}\n"
                "MISSION : Créer une fiche de révision synthétique, mnémotechnique et structurée pour les examens.\n"
                "Format JSON obligatoire :\n"
                "{\n"
                '  "title": "Titre de la fiche",\n'
                '  "definitions": [{"term": "Terme", "definition": "Définition précise sourcée [x]"}],\n'
                '  "key_formulas_or_rules": ["Formule ou règle 1", "Règle 2"],\n'
                '  "frequent_mistakes": ["Piège classique à éviter"],\n'
                '  "quick_qa": [{"question": "Question type", "answer": "Réponse brève"}]\n'
                "}"
            )
        return system_instruction, user_prompt, f"revision-sheet-{self.VERSION}"

    def get_lesson_prompt(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
    ) -> tuple[str, str, str]:
        """Generates prompts for structured pedagogical course/lesson generation.

        Supports hierarchical course outputs with chapters, sections, learning objectives,
        and explanations adapted to the target learner level and language.
        """
        lang = (language or "fr").lower()
        system_instruction = self._get_system_instruction(lang)
        level_directive = self._get_level_directive(level, lang)
        focus_directive = f"\nFOCUS PARTICULIER : {focus}" if focus else ""

        if lang == "ar":
            user_prompt = (
                f"المستند : « {document_title} »\n\n"
                f"المصادر والفقرات المتاحة :\n{context}\n\n"
                f"توجيه المستوى : {level_directive}{focus_directive}\n"
                "المهمة : تحويل هذا المحتوى إلى مقرر تعليمي متكامل، مقسم إلى فصول ودروس تدريجية غنية بالشروحات والأمثلة.\n"
                "هيكل JSON الإلزامي :\n"
                "{\n"
                '  "title": "عنوان الدورة أو المقرر",\n'
                '  "description": "مقدمة شاملة وأهداف عامة للدورة",\n'
                f'  "level": "{level.upper()}",\n'
                '  "learning_objectives": ["هدف عام 1", "هدف عام 2"],\n'
                '  "chapters": [\n'
                "    {\n"
                '      "title": "عنوان الفصل 1",\n'
                '      "summary": "ملخص المحور الأول",\n'
                '      "estimated_minutes": 30,\n'
                '      "sections": [\n'
                "        {\n"
                '          "title": "عنوان الدرس 1.1",\n'
                '          "content": "شرح مفصل وواضح مع أمثلة وتوثيق من المصدر [1]",\n'
                '          "summary": "خلاصة الدرس",\n'
                '          "objectives": ["الهدف الإجرائي من الدرس"],\n'
                '          "estimated_minutes": 15\n'
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ],\n"
                '  "conclusion": "خاتمة وتقييم شامل للمكتسبات"\n'
                "}"
            )
        elif lang == "en":
            user_prompt = (
                f'DOCUMENT: "{document_title}"\n\n'
                f"AVAILABLE SOURCES:\n{context}\n\n"
                f"LEVEL DIRECTIVE: {level_directive}{focus_directive}\n"
                "MISSION: Transform this document content into a comprehensive educational course with chapters and lessons.\n"
                "Mandatory JSON format:\n"
                "{\n"
                '  "title": "Course Title",\n'
                '  "description": "Course introduction and pedagogical context",\n'
                f'  "level": "{level.upper()}",\n'
                '  "learning_objectives": ["Overall objective 1", "Overall objective 2"],\n'
                '  "chapters": [\n'
                "    {\n"
                '      "title": "Chapter 1 Title",\n'
                '      "summary": "Summary of chapter 1",\n'
                '      "estimated_minutes": 30,\n'
                '      "sections": [\n'
                "        {\n"
                '          "title": "Lesson 1.1 Title",\n'
                '          "content": "Detailed educational explanation with practical examples and source citations [1]",\n'
                '          "summary": "Lesson summary",\n'
                '          "objectives": ["Target objective for this lesson"],\n'
                '          "estimated_minutes": 15\n'
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ],\n"
                '  "conclusion": "Summary of learning outcomes and key takeaways"\n'
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
                f"DIRECTIVE DE NIVEAU : {level_directive}{focus_directive}\n"
                "MISSION : Transformer le contenu documentaire en un cours d'apprentissage fluide, progressif et structuré en chapitres et leçons.\n"
                "Format JSON obligatoire :\n"
                "{\n"
                '  "title": "Titre du cours",\n'
                '  "description": "Introduction et contexte pédagogique",\n'
                f'  "level": "{level.upper()}",\n'
                '  "learning_objectives": ["Objectif global 1", "Objectif global 2"],\n'
                '  "chapters": [\n'
                "    {\n"
                '      "title": "Titre du Chapitre 1",\n'
                '      "summary": "Synthèse du chapitre 1",\n'
                '      "estimated_minutes": 30,\n'
                '      "sections": [\n'
                "        {\n"
                '          "title": "Titre de la Leçon 1.1",\n'
                '          "content": "Contenu pédagogique détaillé avec exemples concrets et citations [1]",\n'
                '          "summary": "Résumé de la leçon",\n'
                '          "objectives": ["Objectif d\'apprentissage de cette leçon"],\n'
                '          "estimated_minutes": 15\n'
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ],\n"
                '  "conclusion": "Synthèse et bilan des acquis"\n'
                "}"
            )
        return system_instruction, user_prompt, f"lesson-{self.VERSION}"
