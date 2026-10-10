# RAPPORT TECHNIQUE ET AUDIT — SPRINT 11
## Parcours d'apprentissage, progression et personnalisation

---

### 1. Diagnostic Initial

L'inspection de l'architecture existante d'Amanus Learn AI a révélé les éléments suivants :
- **Modèles de progression préexistants** : `LearningPath` (inscription globale et progression au niveau du cours), `LearningProgress` (progression granulaire par section de cours), `StudySession` (suivi temporel des sessions d'étude).
- **Modèles d'évaluations préexistants** : `Quiz`, `QuizQuestion`, `QuizAnswer`, `QuizAttempt`.
- **Limites et anomalies identifiées avant Sprint 11** :
  1. `LearningProgress` ne stockait qu'un `completion_percent` brut sans distinguer explicitement une section simplement consultée d'une section déclarée terminée (`is_completed`, `completed_at`, `last_viewed_at`).
  2. L'ouverture d'une leçon via l'API risquait de valider la leçon à 100% par défaut au lieu de préserver l'état de consultation en cours.
  3. L'algorithme de reprise (`continue_learning`) risquait de boucler indéfiniment sur le dernier chapitre d'un cours même quand celui-ci était achevé à 100%.
  4. La soumission de quiz dans `QuizAttemptService` n'utilisait pas de verrouillage transactionnel explicite (`select_for_update`), exposant l'API à des soumissions concurrentes ou des rejeux d'évaluations déjà finalisées.
  5. L'API d'historique de quiz ne distinguait pas formellement le meilleur score (`best_score`), le dernier score (`latest_score`) et ne proposait pas d'endpoint paginé pour l'historique global de l'apprenant.

---

### 2. Architecture et Modèles Déployés

#### 2.1 Modèle de Progression Réutilisé et Enrichi
- **Table `learning_learningprogress`** :
  - `is_completed` : Booléen indexé indiquant si la section est déclarée formellement terminée.
  - `completed_at` : Horodatage d'achèvement effectif.
  - `last_viewed_at` : Horodatage de la dernière consultation ou interaction.
  - `completion_percent` : Pourcentage non-décroissant (`max(actuel, nouveau)`), bridé à 99% tant que non validé.
  - `last_position` : Curseur de défilement / position de lecture en pixels/caractères.
  - Contrainte d'unicité `unique_together = ("user", "section")`.
- **Modèle `LearningPath`** :
  - Calcul déterministe `recalculate_progress()` fondé sur le ratio des sections complétées.
  - Transitions d'état strictes : `NOT_STARTED` → `IN_PROGRESS` → `COMPLETED`.

#### 2.2 Règles de Complétion Déterministes
- **Consultation** : L'envoi d'une position de lecture ou d'un pourcentage < 100% sans `is_completed=True` met à jour `last_position` et `last_viewed_at`, conserve le statut `IN_PROGRESS` et ne fixe aucun `completed_at`.
- **Complétion** : Déclenchée soit par `is_completed=True`, soit par l'atteinte de `completion_percent >= 100.0`. Fixe `completion_percent = 100.0`, `is_completed = True` et `completed_at = timezone.now()`.

#### 2.3 Reprise Intelligente de l'Apprentissage (`continue_learning`)
- Examine les parcours actifs inscrits par ordre de dernière activité.
- Identifie la première section non complétée (`is_completed=False` et `completion_percent < 100.0`).
- Restitue le contexte complet : identifiants cours/section, titre, ordre, progression globale et dernière position (`last_position`).
- **Sortie propre de boucle** : Si l'ensemble des cours inscrits est achevé, renvoie `None` au lieu de recommander en boucle une section déjà validée.
- **Résilience** : Gère en toute sécurité la modification ou suppression ultérieure de cours ou chapitres.

#### 2.4 Évaluation et Scoring Serveur
- **Calcul 100% côté serveur** : Les réponses du client (`{question_id: answer_id}`) sont validées contre `QuizAnswer.is_correct` en base de données. Aucun score fourni par le navigateur n'est pris en compte.
- **Verrouillage concurrentiel** : `with transaction.atomic(): QuizAttempt.objects.select_for_update().get(...)` élimine les risques de race conditions et rejette avec `HTTP 409 Conflict` toute tentative de re-soumission d'une tentative déjà clôturée.
- **Distinction explicite** : L'API expose formellement `best_score`, `latest_score`, `best_attempt_id`, `latest_attempt_id`, `average_score` et `total_attempts`.

#### 2.5 Recommandations Déterministes et Explicables
- **Priorité 1 (Notions faibles)** : Tout score < 60% (quiz ou évaluation de chapitre) génère une recommandation explicite indiquant la raison chiffrée et la citation source / objectif associé.
- **Priorité 2 (Cours en cours)** : Reprise des cours commencés mais incomplets.
- **Priorité 3 (Nouveaux cours)** : Démarrage des cours inscrits au programme.
- **Respect de l'état vide** : Aucun contenu factice ou faiblesse inventée n'est injecté pour un utilisateur débutant sans historique.

---

### 3. Fichiers et Composants Modifiés

1. `apps/api/apps/learning/models.py` :
   - Ajout des champs `is_completed`, `completed_at`, `last_viewed_at` à `LearningProgress`.
   - Durcissement de la méthode `recalculate_progress` sur `LearningPath`.
2. `apps/api/apps/learning/migrations/0002_learningprogress_completed_at_and_more.py` :
   - Migration Django non destructrice et rétrocompatible.
3. `apps/api/apps/learning/serializers.py` :
   - Exposition de `is_completed`, `completed_at`, `last_viewed_at` dans `LearningProgressSerializer`.
   - Prise en charge du paramètre optionnel `is_completed` dans `SectionCompleteRequestSerializer`.
4. `apps/api/apps/learning/services/learning_engine.py` :
   - Mise à jour de `record_section_progress`, `get_course_progress`, `get_student_dashboard`, `_find_continue_learning`, `_find_weak_topics`, `_build_recommended_revisions`.
   - Intégration de `recent_quiz_results` dans le dashboard apprenant.
5. `apps/api/apps/learning/views.py` :
   - Transmission des paramètres de complétion et vérification de permissions multi-tenants.
6. `apps/api/apps/quizzes/services/attempt_service.py` :
   - Verrouillage transactionnel avec `select_for_update` sur `submit_attempt`.
   - Synchronisation d'instance et calcul strict serveur.
7. `apps/api/apps/quizzes/views.py` :
   - Enrichissement de `QuizResultsHistoryView` avec `latest_score`, `best_score`, `best_attempt_id`, `latest_attempt_id`, `average_score`.
   - Création de `UserQuizHistoryView` (`GET /api/v1/quizzes/history/`) avec pagination.
8. `apps/api/apps/quizzes/urls.py` :
   - Enregistrement de la route `history/`.
9. `apps/api/tests/test_learning_progression_sprint11.py` :
   - Suite de 12 tests automatisés couvrant exhaustivement tous les critères d'acceptation.
10. `apps/web/types/learning.ts` :
    - Ajout des types `RecentQuizResultItem` et de la propriété optionnelle `is_completed`.
11. `scripts/generate_docx_report.py` :
    - Intégration de la section 3.11 et mise à jour du bilan de validation à 376 tests backend + 32 frontend.

---

### 4. Résultats des Tests Exécutés

- **Backend Pytest** :
  - `apps/api/tests/test_learning_progression_sprint11.py` : **12 / 12 tests passés** (100%).
  - `apps/api/tests/test_learning.py` : **10 / 10 tests passés** (100%).
  - `apps/api/tests/test_quizzes.py` : **15 / 15 tests passés** (100%).
  - **Ensemble de la suite backend** : **376 / 376 tests passés** (0 échec, 0 régression).
- **Frontend Vitest** :
  - **32 / 32 tests passés** (8 suites de test, 100%).
- **Linter Ruff** :
  - **0 erreur, 0 avertissement** (`All checks passed!`).
