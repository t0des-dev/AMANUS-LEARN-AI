# SPRINT 12 — LEARNING ENGINE

## 1. Objectifs & Vue d'ensemble

Le Sprint 12 implémente le moteur d'apprentissage adaptatif (**Learning Engine**) d'Amanus Learn AI. Il transforme la plateforme en un système d'apprentissage complet avec suivi granulaire de la progression de l'apprenant, calcul du temps d'étude effectif, identification automatique des notions à consolider (chapitres faibles), reprise d'apprentissage intelligente et recommandations pédagogiques ciblées.

---

## 2. Modèles de Données

Les modèles sont définis dans `apps/api/apps/learning/models.py` :

### `LearningPath`
Représente l'inscription et la progression globale d'un utilisateur dans un cours :
- `user` : ForeignKey vers l'utilisateur apprenant
- `course` : ForeignKey vers le `Course`
- `status` : Choix (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`)
- `progress` : Progression globale en pourcentage (0.0 à 100.0%)
- `started_at` : Date du premier module démarré
- `completed_at` : Date de complétion intégrale (100%)
- Méthode : `recalculate_progress()` recalcule dynamiquement le pourcentage global en fonction des chapitres validés dans `LearningProgress`.

### `LearningProgress`
Suit la progression granulaire et la performance d'un utilisateur sur un chapitre ou une section :
- `user` : ForeignKey vers l'apprenant
- `course` : ForeignKey vers le cours
- `section` : ForeignKey vers le `CourseSection`
- `completion_percent` : Pourcentage de lecture / complétion de la section (0.0 à 100.0%)
- `last_position` : Position de défilement ou repère de lecture sauvegardé
- `score` : Score de maîtrise ou note obtenue au quiz lié (%)
- Contrainte d'unicité : `("user", "section")`

### `StudySession`
Mesure le temps effectif passé par l'étudiant sur une formation :
- `user` : ForeignKey vers l'apprenant
- `course` : ForeignKey vers le cours étudié
- `started_at` : Heure de début de la session d'étude
- `ended_at` : Heure de fin de la session
- `duration` : Durée nette calculée en secondes
- Méthode : `finish()` calcule `(ended_at - started_at).total_seconds()` et enregistre la session.

---

## 3. Moteur Pédagogique (`LearningEngine`)

Situé dans `apps/api/apps/learning/services/learning_engine.py` :

- **Aucune donnée fictive en production** : Toutes les métriques proviennent des données réelles enregistrées dans PostgreSQL.
- **Continuer l'apprentissage (`continue_learning`)** : Identifie le cours actif le plus récent et pointe précisément sur le premier chapitre non validé ainsi que la dernière position de lecture.
- **Temps d'étude (`total_study_time_seconds`)** : Somme réelle des durées de `StudySession`.
- **Score de maîtrise (`average_score`)** : Moyenne arithmétique réelle combinant les `QuizAttempt` et les notes de `LearningProgress`.
- **Chapitres faibles (`weak_topics`)** : Détection des chapitres ou quiz où l'apprenant a obtenu un score inférieur au seuil de maîtrise ($< 60\%$).
- **Recommandations IA (`recommended_revision`)** : Priorisation des notions fragiles pour révision ciblée, suivie des cours en cours d'achèvement.

---

## 4. Endpoints API (`/api/v1/learning/`)

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/v1/learning/dashboard/` | Tableau de bord de l'apprenant avec métriques réelles (temps, score, chapitres faibles, reprise) |
| `GET` | `/api/v1/learning/courses/` | Liste des parcours de formation suivis par l'utilisateur |
| `GET` | `/api/v1/learning/courses/{id}/progress/` | Détail de progression par section, sections restantes et chapitres faibles du cours |
| `POST` | `/api/v1/learning/sections/{id}/complete/` | Enregistre la complétion d'un chapitre (pourcentage, position, score) et recalcule le parcours |
| `POST` | `/api/v1/learning/sessions/start/` | Démarre une session d'étude chronométrée pour un cours |
| `POST` | `/api/v1/learning/sessions/{id}/finish/` | Clôture une session d'étude et calcule la durée en secondes |

---

## 5. Composants Next.js & Dashboard Étudiant

Intégrés dans `apps/web/app/dashboard/page.tsx` et `apps/web/app/learning/page.tsx` :

1. **`ContinueLearningCard`** :
   - Carte héroïque mettant en valeur la dernière notion en cours.
   - Barre de progression dynamique avec badge de chapitre.
   - Bouton d'action directe « Reprendre la leçon ».
2. **`LearningStatsGrid`** :
   - 4 indicateurs clés : Temps d'étude effectif formaté, Modules complétés, Parcours en cours / terminés, Score moyen de maîtrise.
3. **`WeakTopicsList`** :
   - Affichage des chapitres où le score est inférieur à 60%.
   - Badges de score et liens directs de révision ciblée.
   - État vide valorisant si toutes les notions sont maîtrisées.
4. **`RecentActivityList`** :
   - Historique des sessions d'étude récentes avec durée et date.
5. **`RecommendedRevisionList`** :
   - Recommandations intelligentes priorisant les notions faibles et la continuité des cours.

---

## 6. Tests & Validation

- `LearningEngineUnitTests` : Calculs de progression, complétion automatique à 100%, calcul de la durée des sessions d'étude, détection des chapitres faibles.
- `LearningAPITests` : Couverture complète des endpoints `/learning` avec authentification JWT, pagination et isolation multi-tenant.
- **100% des tests passants** : 166/166 tests Django au total.
