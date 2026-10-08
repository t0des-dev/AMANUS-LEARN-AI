# SPRINT 13 — ANALYTICS

## 1. Objectifs & Vue d'ensemble

Le Sprint 13 implémente le système complet d'analytique pédagogique (**Analytics**) pour les apprenants et les enseignants au sein d'Amanus Learn AI.

Le module repose intégralement sur des métriques réelles (aucun mock en production) issues des modèles `LearningProgress`, `StudySession`, `QuizAttempt`, `QuizQuestion` et `LearningPath`. Il garantit une stricte isolation multi-tenant et respecte les privilèges de rôles (les étudiants n'ont pas accès aux statistiques de cohorte ou aux données d'autres apprenants ; les enseignants n'accèdent qu'aux cours de leur organisation).

---

## 2. Métriques & Calculs

### Analytics Étudiant
- **Temps d'étude** : Durée cumulée des sessions d'étude actives (`StudySession.duration`), avec découpage journalier sur les 7 derniers jours.
- **Cours terminés / en cours** : Nombre de parcours achevés (`LearningPathStatus.COMPLETED`) vs inscrits.
- **Score moyen** : Moyenne arithmétique réelle sur l'ensemble des tentatives de quiz (`QuizAttempt.score`).
- **QCM effectués & Taux de réussite** : Total des tentatives et ratio des examens réussis (`passed = True`).
- **Progression** : Progression moyenne globale et suivi individuel par cours.

### Analytics Enseignant
- **Nombre d'étudiants** : Nombre total d'apprenants inscrits sur le cours (`LearningPath`).
- **Progression moyenne & Taux d'achèvement** : Moyenne des pourcentages de complétion de la cohorte et proportion d'étudiants ayant finalisé le cours.
- **Score moyen & Taux de réussite** : Performance moyenne aux QCM associés au cours.
- **Chapitres problématiques** : Détection automatique des chapitres présentant un taux d'abandon élevé ($< 50\%$) ou une moyenne de score faible ($< 60\%$).
- **Questions difficiles** : Analyse des données de réponses soumises (`QuizAttempt.answers_data`) pour identifier les questions ayant le taux d'erreur le plus élevé.
- **Suivi nominatif des étudiants** : Temps d'étude, note moyenne, état d'avancement et date de dernière activité.

---

## 3. Endpoints API (`/api/v1/analytics/`)

| Méthode | Route | Rôle requis | Description |
|---|---|---|---|
| `GET` | `/api/v1/analytics/student/` | Apprenant connecté | Statistiques personnelles, assiduité sur 7 jours et historique des scores |
| `GET` | `/api/v1/analytics/courses/{id}/` | Enseignant / Admin | Métriques de cohorte, progression moyenne et chapitres problématiques |
| `GET` | `/api/v1/analytics/courses/{id}/students/` | Enseignant / Admin | Tableau de bord individuel des étudiants inscrits au cours |
| `GET` | `/api/v1/analytics/quizzes/{id}/` | Enseignant / Admin | Analyse du quiz avec classement des questions les plus difficiles |

---

## 4. Composants Next.js

Créés dans `apps/web/components/analytics/` :

1. **`ProgressChart`** : Barres de progression d'apprentissage globale et par formation.
2. **`ScoreChart`** : Histogramme visuel de l'historique des notes aux QCM avec indicateurs de réussite.
3. **`StudyTimeChart`** : Histogramme des 7 derniers jours illustrant les minutes d'étude effectives.
4. **`CourseAnalytics`** : Vue d'ensemble de la cohorte avec détection des chapitres problématiques.
5. **`StudentPerformance`** : Tableau de bord nominatif des apprenants avec recherche et filtrage.

Pages créées :
- [`/analytics`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/web/app/analytics/page.tsx) : Espace statistiques pour l'étudiant.
- [`/teacher/analytics`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/web/app/teacher/analytics/page.tsx) : Espace analytique pour l'enseignant avec sélecteur de cours.

---

## 5. Sécurité & Isolation Multi-Tenant

- Vérification systématique de l'appartenance à l'organisation via `CanViewTeacherAnalytics`.
- Les étudiants tentant d'accéder aux routes `/analytics/courses/` ou `/analytics/quizzes/` reçoivent une réponse `403 Forbidden`.
- Les enseignants d'une organisation tierce ne peuvent en aucun cas inspecter les données de cours d'une autre organisation.

---

## 6. Tests & Validation

- `AnalyticsAggregationUnitTests` : Validation des agrégations de temps d'étude, des scores, de la détection des chapitres problématiques et du calcul du taux d'erreur des questions difficiles.
- `AnalyticsAPIPermissionsTests` : Couverture complète des règles de permissions et d'isolation multi-tenant.
- **100% des tests passants** : 9 tests analytiques dédiés + 166 tests précédents = 175 tests Django réussis (`pytest`).
