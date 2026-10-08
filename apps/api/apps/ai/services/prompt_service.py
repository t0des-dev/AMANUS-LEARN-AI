class PromptService:
    """Manages prompt engineering, system instructions, and explicit prompt versioning."""

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

    def get_summary_prompt(self, document_title: str, context: str) -> tuple[str, str, str]:
        """Generates system, user prompt, and prompt version for document summary."""
        user_prompt = (
            f"DOCUMENT : « {document_title} »\n\n"
            f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
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
        return self.BASE_SYSTEM_INSTRUCTION, user_prompt, f"summary-{self.VERSION}"

    def get_key_points_prompt(self, document_title: str, context: str) -> tuple[str, str, str]:
        """Generates prompts for extracting essential key points and core concepts."""
        user_prompt = (
            f"DOCUMENT : « {document_title} »\n\n"
            f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
            "MISSION : Extraire les notions essentielles et points clés à retenir absolument.\n"
            "Format JSON obligatoire :\n"
            "{\n"
            '  "key_points": [\n'
            '    {"point": "Nom de la notion ou règle", "explanation": "Explication détaillée sourcée [x]"}\n'
            "  ]\n"
            "}"
        )
        return self.BASE_SYSTEM_INSTRUCTION, user_prompt, f"key-points-{self.VERSION}"

    def get_objectives_prompt(self, document_title: str, context: str) -> tuple[str, str, str]:
        """Generates prompts for educational learning objectives."""
        user_prompt = (
            f"DOCUMENT : « {document_title} »\n\n"
            f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
            "MISSION : Définir les objectifs pédagogiques (selon la taxonomie d'apprentissage : Comprendre, Appliquer, Analyser, Évaluer).\n"
            "Format JSON obligatoire :\n"
            "{\n"
            '  "objectives": [\n'
            '    {"level": "Comprendre / Appliquer / etc.", "objective": "Objectif formulé avec verbe d\'action"}\n'
            "  ]\n"
            "}"
        )
        return self.BASE_SYSTEM_INSTRUCTION, user_prompt, f"objectives-{self.VERSION}"

    def get_revision_sheet_prompt(self, document_title: str, context: str) -> tuple[str, str, str]:
        """Generates prompts for revision sheet (fiche de révision)."""
        user_prompt = (
            f"DOCUMENT : « {document_title} »\n\n"
            f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
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
        return self.BASE_SYSTEM_INSTRUCTION, user_prompt, f"revision-sheet-{self.VERSION}"

    def get_lesson_prompt(self, document_title: str, context: str) -> tuple[str, str, str]:
        """Generates prompts for structured pedagogical course/lesson generation."""
        user_prompt = (
            f"DOCUMENT : « {document_title} »\n\n"
            f"SOURCES DOCUMENTAIRES DISPONIBLES :\n{context}\n\n"
            "MISSION : Transformer le contenu documentaire en une leçon d'apprentissage fluide, vulgarisée et didactique.\n"
            "Format JSON obligatoire :\n"
            "{\n"
            '  "title": "Titre du cours",\n'
            '  "introduction": "Introduction et contexte",\n'
            '  "sections": [\n'
            '    {"title": "Titre de section", "content": "Contenu pédagogique détaillé"}\n'
            "  ],\n"
            '  "conclusion": "Synthèse et bilan des acquis"\n'
            "}"
        )
        return self.BASE_SYSTEM_INSTRUCTION, user_prompt, f"lesson-{self.VERSION}"
