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
        summary_level: str = "synthetic",
    ) -> tuple[str, str, str]:
        """Generates system, user prompt, and prompt version for multi-tier document summary.

        Supports summary_level:
        - 'very_short': Flashcard / memo summary in 1 concise paragraph (<= 100 words) and 3 core bullets.
        - 'synthetic': Standard pedagogical synthesis in 2-3 structured paragraphs and core takeaways.
        - 'detailed': In-depth chapter-by-chapter analytical summary with conceptual relations and limitations.
        """
        lang = (language or "fr").lower()
        system_instruction = self._get_system_instruction(lang)
        level_directive = self._get_level_directive(level, lang)
        focus_directive = f"\nFOCUS PARTICULIER : {focus}" if focus else ""
        norm_summary_level = str(summary_level).lower().strip()
        if norm_summary_level not in ("very_short", "synthetic", "detailed"):
            norm_summary_level = "synthetic"

        if norm_summary_level == "very_short":
            mission_fr = "Rédiger un résumé TRÈS COURT (fiche mémo flash) de ce document : 1 seul paragraphe concis (max 100 mots) et exactement 3 points clés essentiels."
            format_fr = (
                "{\n"
                '  "summary_level": "very_short",\n'
                '  "overview": "Synthèse ultra-concise en un paragraphe court",\n'
                '  "key_takeaways": ["Point essentiel 1 [x]", "Point essentiel 2 [x]", "Point essentiel 3 [x]"],\n'
                '  "chapters_summary": []\n'
                "}"
            )
        elif norm_summary_level == "detailed":
            mission_fr = "Rédiger un résumé DÉTAILLÉ et approfondi de ce document, structuré par chapitre, explicitant les relations entre concepts, les définitions majeures et les limites/conditions mentionnées dans les sources."
            format_fr = (
                "{\n"
                '  "summary_level": "detailed",\n'
                '  "overview": "Synthèse exhaustive en 3-4 paragraphes avec mise en perspective",\n'
                '  "key_takeaways": ["Point clé 1 [x]", "Point clé 2 [x]", "Point clé 3 [x]", "Point clé 4 [x]"],\n'
                '  "chapters_summary": [\n'
                '    {"title": "Chapitre 1", "summary": "Analyse approfondie du chapitre 1 avec définitions et limites [x]"}\n'
                "  ],\n"
                '  "limitations_and_context": ["Condition de validité ou limite mentionnée dans les sources [x]"]\n'
                "}"
            )
        else:  # synthetic
            mission_fr = "Rédiger un résumé SYNTHÉTIQUE équilibré de ce document : vue d'ensemble en 2-3 paragraphes et notions pivots."
            format_fr = (
                "{\n"
                '  "summary_level": "synthetic",\n'
                '  "overview": "Synthèse globale en 2-3 paragraphes",\n'
                '  "key_takeaways": ["Point clé 1 avec source [x]", "Point clé 2..."],\n'
                '  "chapters_summary": [\n'
                '    {"title": "Titre du chapitre ou partie", "summary": "Résumé du chapitre"}\n'
                "  ]\n"
                "}"
            )

        if lang == "ar":
            user_prompt = (
                f"المستند المرجعي : « {document_title} »\n\n"
                f"المصادر والفقرات المتاحة :\n{context}\n\n"
                f"توجيه المستوى : {level_directive}{focus_directive}\n"
                f"المهمة : إعداد ملخص تعليمي بمستوى ({norm_summary_level}) موثق بالإحالات.\n"
                f"هيكل JSON الإلزامي :\n{format_fr}"
            )
        elif lang == "en":
            user_prompt = (
                f'DOCUMENT: "{document_title}"\n\n'
                f"AVAILABLE SOURCES:\n{context}\n\n"
                f"LEVEL DIRECTIVE: {level_directive}{focus_directive}\n"
                f"MISSION: Write an educational summary at level ({norm_summary_level}) strictly grounded in sources.\n"
                f"Mandatory JSON format:\n{format_fr}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
                f"DIRECTIVE DE NIVEAU : {level_directive}{focus_directive}\n"
                f"MISSION : {mission_fr}\n"
                f"Format JSON obligatoire :\n{format_fr}"
            )
        summary_ver = (
            f"summary-{self.VERSION}"
            if norm_summary_level == "synthetic"
            else f"summary-{norm_summary_level}-{self.VERSION}"
        )
        return system_instruction, user_prompt, summary_ver

    def get_blueprint_prompt(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
    ) -> tuple[str, str, str]:
        """Generates prompts for extracting the central Pedagogical Blueprint (Sprint 10)."""
        lang = (language or "fr").lower()
        system_instruction = self._get_system_instruction(lang)
        level_directive = self._get_level_directive(level, lang)
        focus_directive = f"\nFOCUS PARTICULIER : {focus}" if focus else ""

        user_prompt = (
            f"DOCUMENT SOURCE : « {document_title} »\n\n"
            f"EXTRAITS DOCUMENTAIRES VALIDES :\n{context}\n\n"
            f"NIVEAU ÉDUCATIF : {level_directive}{focus_directive}\n"
            "MISSION : Extraire la structure pédagogique maîtresse (Base Pédagogique Commune) servant de pivot "
            "pour dériver cours, résumés multi-niveaux, quiz alignés, diapositives et capsules audio.\n\n"
            "RÈGLES STRICTES :\n"
            "1. Séparez rigoureusement les faits tirés des documents sources ('source_facts') des exemples pédagogiques créés pour illustrer ('pedagogical_examples').\n"
            "2. Formulez des objectifs d'apprentissage mesurables avec verbes d'action (Comprendre, Appliquer, Analyser).\n"
            "3. Associez à chaque concept clé sa définition canonique et sa référence source [x].\n\n"
            "Format JSON obligatoire :\n"
            "{\n"
            f'  "title": "{document_title}",\n'
            '  "subject": "Thématique principale du document",\n'
            '  "target_audience": "Public cible visé",\n'
            f'  "level": "{level.upper()}",\n'
            '  "prerequisites": ["Prérequis 1", "Prérequis 2"],\n'
            '  "learning_objectives": [\n'
            '    {"id": "obj_1", "taxonomy_level": "Comprendre", "description": "Objectif 1", "source_ref": "[1]"}\n'
            '  ],\n'
            '  "key_concepts": [\n'
            '    {"term": "Terme clé", "canonical_definition": "Définition rigoureuse", "importance": "CORE", "source_ref": "[1]"}\n'
            '  ],\n'
            '  "sections_outline": [\n'
            '    {\n'
            '      "order": 1,\n'
            '      "title": "Titre du chapitre ou de la section",\n'
            '      "key_explanation": "Explication théorique centrale",\n'
            '      "source_facts": ["Fait avéré extrait du document [1]"],\n'
            '      "pedagogical_examples": ["Exemple concret pour faciliter l\'assimilation"],\n'
            '      "summary": "Synthèse du chapitre",\n'
            '      "estimated_minutes": 20\n'
            '    }\n'
            '  ],\n'
            '  "key_takeaways": ["Point essentiel à retenir 1", "Point essentiel 2"],\n'
            '  "self_assessment_checks": ["Question de vérification des acquis 1"]\n'
            "}"
        )
        return system_instruction, user_prompt, f"blueprint-{self.VERSION}"

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

    def get_slides_prompt(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
        slide_count: int | None = None,
    ) -> tuple[str, str, str]:
        """Generates prompts for a full RAG-grounded slide deck from a document."""
        lang = (language or "fr").lower()
        system_instruction = self._get_system_instruction(lang)
        focus_directive = f"\nFOCUS PARTICULIER : {focus}" if focus else ""
        count_directive = (
            f"\nNOMBRE DE DIAPOSITIVES CIBLÉ : {slide_count}" if slide_count else ""
        )

        if lang == "ar":
            user_prompt = (
                f"المستند : « {document_title} »\n\n"
                f"المصادر المتاحة :\n{context}\n{focus_directive}{count_directive}\n"
                "المهمة : تصميم عرض تقديمي تعليمي متكامل ومتسلسل انطلاقاً من هذا المستند.\n"
                "قواعد صارمة :\n"
                "- استند في كل عبارة إلى المصادر ووثّقها بالإحالات [x].\n"
                "- ابدأ بشريحة عنوان، ثم جدول أعمال، ثم المحتوى، ثم خلاصة، ثم خاتمة.\n"
                "- بين 4 و6 نقاط كحد أقصى لكل شريحة، صياغة موجزة في سطر واحد لكل نقطة.\n"
                "- اضبط المفردات وعمق التحليل على المستوى التعليمي المطلوب.\n"
                "هيكل JSON الإلزامي :\n"
                "{\n"
                '  "slides": [\n'
                '    {\n'
                '      "slide_number": 1,\n'
                '      "title": "عنوان الشريحة",\n'
                '      "bullet_points": ["نقطة موثقة [1]", "نقطة أخرى"],\n'
                '      "speaker_notes": "ملاحظات المتحدث لإحياء هذه الشريحة."\n'
                "    }\n"
                "  ]\n"
                "}"
            )
        elif lang == "en":
            user_prompt = (
                f'DOCUMENT: "{document_title}"\n\n'
                f"AVAILABLE SOURCES:\n{context}\n{focus_directive}{count_directive}\n"
                "MISSION: Design a complete, coherent pedagogical slide deck grounded in this document.\n"
                "Strict rules:\n"
                "- Ground every statement in the sources and cite them with [x].\n"
                "- Start with a title slide, then an agenda, then content, then a summary, then a conclusion.\n"
                "- Between 4 and 6 bullets per slide maximum, each phrased on a single concise line.\n"
                "- Adapt vocabulary and depth to the requested learning level.\n"
                "Mandatory JSON format:\n"
                "{\n"
                '  "slides": [\n'
                "    {\n"
                '      "slide_number": 1,\n'
                '      "title": "Slide title",\n'
                '      "bullet_points": ["Sourced point [1]", "Another point"],\n'
                '      "speaker_notes": "Presenter notes to deliver this slide."\n'
                "    }\n"
                "  ]\n"
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n{focus_directive}{count_directive}\n"
                "MISSION : Concevoir un support de présentation (diaporama) pédagogique complet et cohérent à partir de ce document.\n"
                "Règles strictes :\n"
                "- Appuie chaque affirmation sur les sources et cite les références entre crochets [x].\n"
                "- Commence par une diapositive de titre, puis un sommaire, puis le contenu, puis une synthèse et une conclusion.\n"
                "- Entre 4 et 6 points maximum par diapositive, formulés de façon concise sur une seule ligne chacun.\n"
                "- Adapte le vocabulaire et la profondeur d'analyse au niveau pédagogique demandé.\n"
                "Format JSON obligatoire :\n"
                "{\n"
                '  "slides": [\n'
                "    {\n"
                '      "slide_number": 1,\n'
                '      "title": "Titre de la diapositive",\n'
                '      "bullet_points": ["Point sourcé [1]", "Autre point"],\n'
                '      "speaker_notes": "Notes de l\'intervenant pour animer cette diapositive."\n'
                "    }\n"
                "  ]\n"
                "}"
            )
        return system_instruction, user_prompt, f"slides-{self.VERSION}"

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
                "المهمة الإلزامية :\n"
                "1. تغطية كامل محتوى الوثيقة عبر توليد جميع الفصول التعليمية اللازمة (من 4 إلى 6 فصول كاملة).\n"
                "2. يجب أن يتضمن كل فصل من 2 إلى 3 دروس تفصيلية متدرجة وشاملة تغطي كافة المفاهيم.\n"
                "3. في كل درس، يجب كتابة محتوى تعليمي غني ومنظم بتنسيق Markdown متقن (عناوين فرعية ## و ###، نقاط رئيسية، أمثلة توضيحية، تنبيهات، وإحالات المصادر [1] و [2]).\n"
                "4. تحذير حاسم وإلزامي: يُمنع منعاً باتاً الاكتفاء بالعناوين أو المخططات الهيكلية أو مجرد نقاط مقتضبة. يجب أن يتضمن حقل 'content' في كل درس شرحاً نظرياً وتحليلياً وتطبيقياً متكاملاً في 3 إلى 5 فقرات تعليمية مطولة تشرح المفاهيم باستفاضة تامة مع الاستشهادات [1] و [2] بحيث يستفيد المتعلم من درس تعليمي كامل وغني بالمعارف.\n\n"
                "هيكل JSON الإلزامي :\n"
                "{\n"
                '  "title": "عنوان الدورة أو المقرر الكامل",\n'
                '  "description": "مقدمة شاملة وأهداف عامة للدورة مستخلصة من الوثيقة",\n'
                f'  "level": "{level.upper()}",\n'
                '  "learning_objectives": ["هدف عام 1", "هدف عام 2", "هدف عام 3"],\n'
                '  "chapters": [\n'
                "    {\n"
                '      "title": "الفصل 1 : المقدمة والمفاهيم الأساسية",\n'
                '      "summary": "ملخص شامل للمحور الأول",\n'
                '      "estimated_minutes": 35,\n'
                '      "sections": [\n'
                "        {\n"
                '          "title": "الدرس 1.1 : الإطار العام والمفاهيم الجوهرية",\n'
                '          "content": "## المفاهيم الأساسية\\n\\nيقدم هذا الدرس شرحاً تأصيلياً ومعمقاً للمفاهيم الجوهرية الواردة في الوثيقة [1]. يرتكز التحليل على استيعاب القواعد والآليات التأسيسية التي تشكل المنطلق الفعلي للموضوع.\\n\\n### التطبيقات العملية والمنهجية\\nيتطلب تطبيق هذه المفاهيم اتباع خطوات منهجية دقيقة لضمان تحقيق النتائج المرجوة [2]. وتبرز أهمية الربط بين النظريات والواقع العملي في تلافي الأخطاء الشائعة.\\n\\n### النقاط الرئيسية\\n- المبدأ التأسيسي الأول المستخرج من الوثيقة [1].\\n- المعايير التشغيلية المتبعة في الميدان [2].\\n\\n> **ملاحظة تأطيرية :** يتعين ترسيخ هذه القواعد كأرضية صلبة قبل الانتقال إلى المحاور المتقدمة.",\n'
                '          "summary": "خلاصة الدرس",\n'
                '          "objectives": ["استيعاب المفاهيم الأولية بدقة"],\n'
                '          "estimated_minutes": 15\n'
                "        },\n"
                "        {\n"
                '          "title": "الدرس 1.2 : التعاريف والمحددات التقنية",\n'
                '          "content": "## المعايير والمحددات\\n\\nتحليل معمق للمحددات المستخرجة من الوثيقة [1] مع استعراض النماذج التطبيقية والضوابط المنهجية...\\n\\n### التوجيهات التشغيلية\\nتفصيل الخطوات العملية والأمثلة الواقعية المستندة إلى المراجع [2].",\n'
                '          "summary": "خلاصة الدرس الثاني",\n'
                '          "objectives": ["التمييز بين المعايير والمحددات"],\n'
                '          "estimated_minutes": 20\n'
                "        }\n"
                "      ]\n"
                "    },\n"
                "    {\n"
                '      "title": "الفصل 2 : الهيكلية والآليات التأسيسية",\n'
                '      "summary": "دراسة المكونات والآليات",\n'
                '      "estimated_minutes": 40,\n'
                '      "sections": [\n'
                "        {\n"
                '          "title": "الدرس 2.1 : تحليل المكونات",\n'
                '          "content": "## البنية الهيكلية\\n\\nشرح منهجي ومفصل للمكونات والعلاقات الوظيفية بين عناصر الموضوع مدعماً بالاستشهادات [1] والأمثلة المعيارية [2]...",\n'
                '          "summary": "خلاصة تحليل المكونات",\n'
                '          "objectives": ["تحليل العلاقات بين المكونات"],\n'
                '          "estimated_minutes": 20\n'
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ],\n"
                '  "conclusion": "خاتمة وتقييم شامل للمكتسبات المعرفية للمقرر"\n'
                "}"
            )
        elif lang == "en":
            user_prompt = (
                f'DOCUMENT: "{document_title}"\n\n'
                f"AVAILABLE SOURCES:\n{context}\n\n"
                f"LEVEL DIRECTIVE: {level_directive}{focus_directive}\n"
                "MANDATORY MISSION:\n"
                "1. Cover the entire document breadth by generating all necessary chapters (generate 4 to 6 full chapters).\n"
                "2. Each chapter must contain 2 to 3 detailed, progressive lessons.\n"
                "3. In each lesson, provide rich, substantive educational text in Markdown (subheadings ## and ###, bullet points, concrete examples, notes, and citations [1], [2]).\n"
                "4. CRITICAL MANDATORY DIRECTIVE: STRICTLY FORBIDDEN to output only headings, skeletal outlines, or bare bullet points. The 'content' field of EACH lesson MUST contain a thorough, substantive instructional development of at least 3 to 5 full analytical paragraphs explaining the concepts in detail, providing practical illustrations, and citing sources [1], [2].\n\n"
                "Mandatory JSON format:\n"
                "{\n"
                '  "title": "Comprehensive Course Title",\n'
                '  "description": "Course introduction and pedagogical context grounded in sources",\n'
                f'  "level": "{level.upper()}",\n'
                '  "learning_objectives": ["Overall objective 1", "Overall objective 2", "Overall objective 3"],\n'
                '  "chapters": [\n'
                "    {\n"
                '      "title": "Chapter 1: Foundations & Core Concepts",\n'
                '      "summary": "Summary of chapter 1",\n'
                '      "estimated_minutes": 35,\n'
                '      "sections": [\n'
                "        {\n"
                '          "title": "Lesson 1.1: Theoretical Overview",\n'
                '          "content": "## Foundational Overview\\n\\nThis lesson provides a comprehensive, deep instructional exploration of core concepts grounded in source document [1]. Theoretical frameworks and methodological pillars are clearly defined and contextualized.\\n\\n### Practical Applications & Methodologies\\nApplying these principles effectively requires adhering to tested operational guidelines and structured analytical workflows [2].\\n\\n### Key Principles\\n- Primary foundational insight extracted from source material [1]\\n- Practical guidelines and industry standards [2]\\n\\n> **Important Note:** Master these core foundations before progressing to advanced modules.",\n'
                '          "summary": "Lesson summary",\n'
                '          "objectives": ["Understand foundational concepts"],\n'
                '          "estimated_minutes": 15\n'
                "        },\n"
                "        {\n"
                '          "title": "Lesson 1.2: Technical Terminology & Rules",\n'
                '          "content": "## Definitions & Methodological Rules\\n\\nDetailed breakdown of technical concepts with full source citations [1] and operational illustrations [2]...",\n'
                '          "summary": "Summary of lesson 1.2",\n'
                '          "objectives": ["Master technical terminology"],\n'
                '          "estimated_minutes": 20\n'
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ],\n"
                '  "conclusion": "Synthesis of learning outcomes and key takeaways"\n'
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
                f"DIRECTIVE DE NIVEAU : {level_directive}{focus_directive}\n"
                "MISSION OBLIGATOIRE :\n"
                "1. Couvrir l'INTÉGRALITÉ du document source en générant TOUS les chapitres nécessaires (générer 4 à 6 chapitres complets structurés).\n"
                "2. Chaque chapitre doit comporter 2 à 3 leçons détaillées et progressives pour approfondir le sujet.\n"
                "3. Chaque leçon doit fournir un contenu didactique riche et complet rédigé en Markdown structuré (titres ## et ###, puces didactiques, exemples concrets, encadrés de synthèse et citations de sources [1], [2]).\n"
                "4. DIRECTIVE CRITIQUE OBLIGATOIRE : INTERDICTION STRICTE de renvoyer de simples titres, un sommaire ou des listes à puces squelettiques. Le champ 'content' de chaque leçon DOIT contenir un développement pédagogique complet et approfondi d'au moins 3 à 5 paragraphes substantiels expliquant les notions en détail, illustrant par des exemples concrets et référençant les sources [1], [2].\n\n"
                "Format JSON obligatoire :\n"
                "{\n"
                '  "title": "Titre complet du cours",\n'
                '  "description": "Introduction et contexte pédagogique basés rigoureusement sur le document",\n'
                f'  "level": "{level.upper()}",\n'
                '  "learning_objectives": ["Objectif global 1", "Objectif global 2", "Objectif global 3"],\n'
                '  "chapters": [\n'
                "    {\n"
                '      "title": "Chapitre 1 : Introduction & Fondements Théoriques",\n'
                '      "summary": "Synthèse du premier axe thématique",\n'
                '      "estimated_minutes": 35,\n'
                '      "sections": [\n'
                "        {\n"
                '          "title": "Leçon 1.1 : Cadre Conceptuel et Notions Clés",\n'
                '          "content": "## Fondements et Concepts Clés\\n\\nExplication pédagogique détaillée en plusieurs paragraphes...\\n\\n### Principes directeurs\\n- Premier élément majeur appuyé sur les sources [1]\\n- Second principe fondamental [2]\\n\\n> **Définition clé :** Énoncé précis tiré du document.",\n'
                '          "summary": "Synthèse de la leçon 1.1",\n'
                '          "objectives": ["Assimiler les notions de base"],\n'
                '          "estimated_minutes": 15\n'
                "        },\n"
                "        {\n"
                '          "title": "Leçon 1.2 : Terminologie et Règles Fondamentales",\n'
                '          "content": "## Vocabulaire et Règles Métier\\n\\nPrésentation approfondie des règles extraites du document [1]...",\n'
                '          "summary": "Synthèse de la leçon 1.2",\n'
                '          "objectives": ["Maîtriser la terminologie spécifique"],\n'
                '          "estimated_minutes": 20\n'
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ],\n"
                '  "conclusion": "Synthèse générale et bilan des compétences acquises"\n'
                "}"
            )
        return system_instruction, user_prompt, f"lesson-{self.VERSION}"

    def get_podcast_dialogue_prompt(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
    ) -> tuple[str, str, str]:
        """Generates a dynamic 2-host pedagogical podcast dialogue (Host & Expert / NotebookLM style)."""
        system_instruction = self._get_system_instruction(language)
        level_directive = self._get_level_directive(level, language)
        focus_directive = f"\nFocus spécifique demandé : {focus}" if focus else ""

        lang_code = language.lower() if language in ("fr", "en", "ar") else "fr"

        if lang_code == "en":
            user_prompt = (
                f"DOCUMENT: « {document_title} »\n\n"
                f"AVAILABLE SOURCE CONTEXT:\n{context}\n\n"
                f"LEVEL DIRECTIVE: {level_directive}{focus_directive}\n\n"
                "OBJECTIVE: Create an engaging, high-energy 2-host pedagogical podcast episode (NotebookLM style).\n"
                "Characters:\n"
                "1. Emma (Host) - Curious, relatable, asks intuitive questions, uses everyday analogies, drives pace.\n"
                "2. David (Expert) - Knowledgeable specialist, explains concepts clearly, grounds claims with exact source citations [1], [2], warns against common misconceptions.\n\n"
                "MANDATORY RULES:\n"
                "1. Produce 10 to 16 conversational dialogue turns alternating naturally between Emma and David.\n"
                "2. Ground every technical claim strictly in the provided sources with [1], [2] citations.\n"
                "3. Keep the tone vibrant, educational, accessible, and free of dry reading.\n\n"
                "Required JSON Format:\n"
                "{\n"
                '  "title": "Engaging Podcast Episode Title",\n'
                '  "description": "Short pitch of what listeners will learn in this episode",\n'
                '  "hosts": [\n'
                '    {"name": "Emma", "role": "host", "voice_id": "shimmer"},\n'
                '    {"name": "David", "role": "expert", "voice_id": "onyx"}\n'
                "  ],\n"
                '  "turns": [\n'
                '    {"speaker": "Emma", "role": "host", "text": "Welcome to today\'s deep dive! Today we\'re unpacking..."},\n'
                '    {"speaker": "David", "role": "expert", "text": "Hey Emma! Yes, and looking at our source materials [1], the key mechanism is..."}\n'
                "  ],\n"
                '  "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],\n'
                '  "estimated_duration_minutes": 5\n'
                "}"
            )
        elif lang_code == "ar":
            user_prompt = (
                f"المستند : « {document_title} »\n\n"
                f"سياق المصادر المتوفرة :\n{context}\n\n"
                f"توجيه المستوى : {level_directive}{focus_directive}\n\n"
                "الهدف : إنشاء حلقة بودكاست تعليمية شيقة وتفاعلية بنظام مذيعين اثنين (أسلوب الحوار التفاعلي الحديث).\n"
                "الشخصيات :\n"
                "1. ليلى (المقدمة) - فضولية، تطرح أسئلة ذكية، تقرب المفاهيم بأمثلة من الواقع المعاش.\n"
                "2. كريم (الخبير) - أخصائي متمكن، يحلل المفاهيم بدقة ويستند دائماً إلى المصادر الموثقة [1] و [2].\n\n"
                "الشروط الصارمة :\n"
                "1. توليد حوار غني يتألف من 10 إلى 16 تدخلاً تفاعلياً متبادلاً بسلاسة بين ليلى وكريم.\n"
                "2. توثيق الحقائق بدقة عبر الإحالات [1] و [2].\n\n"
                "صيغة JSON الإلزامية :\n"
                "{\n"
                '  "title": "عنوان جذاب لحلقة البودكاست",\n'
                '  "description": "مقدمة موجزة عما سيتعلمه المستمع في هذه الحلقة",\n'
                '  "hosts": [\n'
                '    {"name": "ليلى", "role": "host", "voice_id": "shimmer"},\n'
                '    {"name": "كريم", "role": "expert", "voice_id": "onyx"}\n'
                "  ],\n"
                '  "turns": [\n'
                '    {"speaker": "ليلى", "role": "host", "text": "أهلاً بكم في عدد جديد من بودكاست المعرفة! موضوعنا اليوم يثير الكثير من التساؤلات..."},\n'
                '    {"speaker": "كريم", "role": "expert", "text": "أهلاً ليلى، وبالفعل، كما توضح وثائقنا المعتمدة [1]، فإن السر يكمن في..."}\n'
                "  ],\n"
                '  "key_takeaways": ["الخلاصة 1", "الخلاصة 2", "الخلاصة 3"],\n'
                '  "estimated_duration_minutes": 5\n'
                "}"
            )
        else:
            user_prompt = (
                f"DOCUMENT : « {document_title} »\n\n"
                f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
                f"DIRECTIVE DE NIVEAU : {level_directive}{focus_directive}\n\n"
                "MISSION : Concevoir un épisode de podcast pédagogique captivant à deux voix (format NotebookLM / Grand Débat).\n"
                "Personnages :\n"
                "1. Camille (L'Hôte) - Dynamique, curieuse, pose les bonnes questions du point de vue de l'apprenant, utilise des métaphores intuitives.\n"
                "2. Alex (L'Expert) - Pédagogue précis, décortique les mécanismes complexes, étaye rigoureusement avec les citations de sources [1], [2], prévient des erreurs courantes.\n\n"
                "RÈGLES IMPÉRATIVES :\n"
                "1. Produire entre 10 et 16 répliques fluides et vivantes alternant naturellement entre Camille et Alex.\n"
                "2. Chaque notion clé doit s'appuyer sur les sources documentaires avec citations [1], [2].\n"
                "3. Rendre la conversation rythmée, stimulante et pédagogiquement accessible sans lecture monotone.\n\n"
                "Format JSON obligatoire :\n"
                "{\n"
                '  "title": "Titre percutant de l\'épisode de podcast",\n'
                '  "description": "Courte présentation accrocheuse des enjeux abordés",\n'
                '  "hosts": [\n'
                '    {"name": "Camille", "role": "host", "voice_id": "shimmer"},\n'
                '    {"name": "Alex", "role": "expert", "voice_id": "onyx"}\n'
                "  ],\n"
                '  "turns": [\n'
                '    {"speaker": "Camille", "role": "host", "text": "Bonjour et bienvenue à tous ! Aujourd\'hui, on décortique un sujet passionnant..."},\n'
                '    {"speaker": "Alex", "role": "expert", "text": "Salut Camille ! Exactement, et ce qui est fascinant dès qu\'on ouvre notre document de référence [1], c\'est que..."}\n'
                "  ],\n"
                '  "key_takeaways": ["Point clé 1", "Point clé 2", "Point clé 3"],\n'
                '  "estimated_duration_minutes": 5\n'
                "}"
            )

        return system_instruction, user_prompt, f"podcast-{self.VERSION}"
