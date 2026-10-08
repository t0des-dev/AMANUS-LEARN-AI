# AMANUS LEARN AI — Vision & Principes Fondateurs

## 1. Vision du Produit
Amanus Learn AI est une plateforme SaaS EdTech / IA / RAG / LMS permettant à un utilisateur d'importer des documents pédagogiques ou professionnels et de les transformer automatiquement en contenus d'apprentissage interactifs et personnalisés.

### Documents supportés
- **Documents textuels et présentations** : PDF, DOCX, PPTX, TXT.
- **Documents numérisés** : OCR & scans haute précision.
- **Extensions futures** : Pages web, HTML, URL, vidéos/transcriptions.

### Artefacts et fonctionnalités générés
1. Résumé général et résumés par chapitre.
2. Cours simplifiés et vulgarisés.
3. Fiches de révision (flashcards).
4. Objectifs pédagogiques et notions essentielles.
5. QCM adaptatifs et examens blancs avec explications détaillées.
6. Cours audio (TTS multi-voix).
7. Présentations et diaporamas de formation.
8. Assistant IA conversationnel sourcé.
9. Parcours d'apprentissage individualisés.
10. Statistiques et analytics d'apprentissage.

---

## 2. Principes Absolus de Développement

### 2.1 Développement par Sprints Autonomes (Sprint 00 → Sprint 14)
- Chaque sprint doit être autonome, testable, documenté, fonctionnel et validé avant le passage au suivant.
- Interdiction stricte de tenter d'implémenter plusieurs sprints en une seule étape.

### 2.2 Protection du Code Existant
- Ne jamais supprimer de fonctionnalité existante sans analyse et validation préalable.
- Respecter scrupuleusement l'intégrité de la base de données et des migrations Django.

### 2.3 Qualité et Rigueur Technique
- Couverture de tests unitaires et d'API systématique.
- Validation des migrations, linting (Ruff), vérification de types (mypy / tsc).
- Cloisonnement multi-tenant strict et vérification des autorisations.

### 2.4 Indépendance IA (Multi-Provider)
- Aucune clé d'API hardcodée.
- Couches d'abstraction obligatoires :
  - `AIProvider` (OpenAI, Anthropic, Gemini, Local LLM / Ollama / vLLM)
  - `EmbeddingProvider`
  - `TTSProvider`
  - `OCRProvider`

### 2.5 RAG Strict & Anti-Hallucination
- Toute réponse dérivée d'un document doit être strictement sourcée (référence document, chapitre, section, page, chunk).
- En l'absence de preuve dans les sources :
  > *"Cette information n'est pas présente dans les documents disponibles."*
