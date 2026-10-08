# SPRINT 08 — QCM ENGINE : Rapport de Réalisation & Validation

## 1. Objectif du Sprint
Créer le moteur complet de QCM (Questionnaire à Choix Multiples) pour **Amanus Learn AI** :
- Modélisation relationnelle complète (`Quiz`, `QuizQuestion`, `QuizAnswer`, `QuizAttempt`).
- 3 modes d'évaluation : **TRAINING** (Entraînement), **EXAM** (Examen certifiant chronométré), **REVISION** (Fiches et révisions adaptatives).
- 3 niveaux de difficulté : **EASY**, **MEDIUM**, **HARD**.
- Génération automatisée par IA assistée par RAG avec **validation JSON stricte** avant insertion.
- Moteur de scoring, de soumission et de suivi des tentatives étudiantes.
- Interfaces Next.js interactives et réactives.

---

## 2. Architecture & Composants Réalisés

### 2.1 Modèles Relationnels (`apps/api/apps/quizzes/models.py`)
- **`Quiz`** :
  - `organization` (FK multi-tenant isolé)
  - `course` (FK optionnelle vers `Course`)
  - `title`, `description`
  - `quiz_type` (`TRAINING`, `EXAM`, `REVISION`)
  - `difficulty` (`EASY`, `MEDIUM`, `HARD`)
  - `time_limit_minutes` (optionnel ou illimité)
  - `passing_score` (seuil de validation en %, par défaut 70%)
  - `is_published` (visibilité pour les apprenants)
- **`QuizQuestion`** :
  - `quiz` (FK vers `Quiz`)
  - `question` (énoncé pédagogique clair)
  - `explanation` (justification pédagogique affichée lors de la correction)
  - `difficulty` (`EASY`, `MEDIUM`, `HARD`)
  - `source` (traçabilité documentaire ou référence du cours)
  - `order` (position dans le questionnaire)
- **`QuizAnswer`** :
  - `question` (FK vers `QuizQuestion`)
  - `text` (intitulé de la réponse)
  - `is_correct` (booléen - masqué aux étudiants avant soumission)
  - `order` (position 1..4)
- **`QuizAttempt`** :
  - `quiz` (FK vers `Quiz`)
  - `user` (FK vers `User`)
  - `score` (score calculé en pourcentage 0..100)
  - `is_passed` (booléen `score >= passing_score`)
  - `total_questions`, `correct_answers`
  - `answers_data` (dictionnaire `{question_id: selected_answer_id}`)
  - `results_breakdown` (analyse question par question avec justification et source)
  - `time_spent_seconds` (durée réelle écoulée)
  - `started_at`, `completed_at`

---

### 2.2 Règle d'Or de Sécurité IA : Validation Stricte avant Insertion
Conformément aux exigences :
> *"Une question générée par IA doit être validée avant insertion. Ne jamais accepter aveuglément une réponse JSON du LLM."*

Le service [`QuizQuestionValidator`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/api/apps/quizzes/services/validator.py) effectue les vérifications suivantes :
1. **Format JSON valide** : dictionnaire avec clés obligatoires `question`, `answers`, `explanation`, `difficulty`, `source`.
2. **Exactement 4 réponses** : rejet systématique si < 4 ou > 4 propositions.
3. **Exactement 1 bonne réponse** : rejet si aucune proposition n'a `is_correct=true` ou si plusieurs en ont.
4. **Non-duplication des réponses** : rejet si deux propositions ont un texte identique.
5. **Non-vacuité** : rejet si l'énoncé ou l'explication fait moins de 5 caractères.

Toute question malformée lève `InvalidQuizQuestionError` et n'est **jamais** insérée dans PostgreSQL.

---

### 2.3 Endpoints API v1 (`apps/api/apps/quizzes/` & `courses/`)

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/courses/{id}/quizzes/` | Lister les quiz d'un cours |
| `POST` | `/api/v1/courses/{id}/quizzes/` | Créer un quiz rattaché à un cours |
| `GET` | `/api/v1/quizzes/` | Catalogue des quiz (filtres par type et difficulté) |
| `POST` | `/api/v1/quizzes/` | Créer un quiz autonome |
| `GET` | `/api/v1/quizzes/{id}/` | Détails d'un quiz (masque `is_correct` pour les étudiants) |
| `POST` | `/api/v1/quizzes/{id}/generate/` | Génération de questions par IA assistée par RAG |
| `POST` | `/api/v1/quizzes/{id}/start/` | Démarrer une nouvelle tentative |
| `POST` | `/api/v1/quizzes/{id}/submit/` | Soumettre les réponses, calculer le score et clore la tentative |
| `GET` | `/api/v1/quizzes/{id}/results/` | Consulter les résultats et la correction détaillée |

---

### 2.4 Interface Frontend Next.js

1. **Composants dédiés (`apps/web/features/quiz/`)** :
   - [`QuizTimer.tsx`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/web/features/quiz/QuizTimer.tsx) : compte à rebours interactif, avertissements visuels (< 2 min, < 30s) et auto-soumission.
   - [`QuizProgress.tsx`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/web/features/quiz/QuizProgress.tsx) : barre de progression et sélecteurs de questions rapides.
   - [`AnswerOption.tsx`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/web/features/quiz/AnswerOption.tsx) : carte de choix multiple (A, B, C, D) avec états actif, survol, sélectionné, et mode correction (vert / rouge).
   - [`QuestionCard.tsx`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/web/features/quiz/QuestionCard.tsx) : présentation de la question, badge de difficulté, citation de la source, options et explication pédagogique.
   - [`QuizCard.tsx`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/web/features/quiz/QuizCard.tsx) : carte d'aperçu d'un quiz dans le catalogue avec badges et bouton Jouer.
   - [`QuizResult.tsx`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/web/features/quiz/QuizResult.tsx) : jauge de score, statut validé/échoué, métriques (correctes, erreurs, temps) et synthèse détaillée avec explications.
2. **Pages de l'application (`apps/web/app/quizzes/`)** :
   - `/quizzes` : Catalogue avec filtres (modes `TRAINING`, `EXAM`, `REVISION` et difficultés), modal de création manuelle et génération IA.
   - `/quizzes/[id]` : Page de présentation, règles du test, consignes et historique des tentatives de l'utilisateur.
   - `/quizzes/[id]/play` : Lecteur de quiz immersif avec chronomètre, navigation questions et modal de confirmation en cas de questions omises.
   - `/quizzes/[id]/results` : Bilan des résultats, score, correction et lien de reprise.

---

## 3. Résultats des Tests & Assurance Qualité

### 3.1 Tests Unitaires & Intégration Backend (`apps/api/tests/test_quizzes.py`)
- **Scoring & Évaluation** : test de score 100% parfait, score partiel avec calcul du seuil `is_passed`.
- **Validation stricte** :
  - Détection et rejet si nombre de choix != 4 (`test_reject_if_not_4_answers`).
  - Détection et rejet si 0 ou > 1 bonne réponse (`test_reject_if_multiple_correct_or_zero_correct`).
  - Détection et rejet de doublons (`test_reject_duplicate_options`).
  - Détection et rejet d'énoncés ou explications vides (`test_reject_empty_question_or_explanation`).
- **Génération IA** : validation avec `MockAIProvider` et vérification de conformité des chunks sources.
- **Permissions & Multi-Tenant** :
  - Seuls les enseignants/admins peuvent créer des quiz (`test_student_cannot_create_quiz`).
  - Masquage strict de `is_correct` pour les étudiants en cours d'épreuve (`test_student_cannot_see_is_correct_flag_in_detail_view`).
  - Isolation inter-organisations (`test_cross_tenant_cannot_access_or_play_quiz`).

### 3.2 Bilan d'Exécution Global
- **Pytest** : **116 / 116 tests validés avec succès** (2.65s).
- **Ruff linter** : `All checks passed!`
- **Ruff format** : `152 files already formatted.`
- **TypeScript** : `tsc --noEmit` compilé sans aucune erreur.
