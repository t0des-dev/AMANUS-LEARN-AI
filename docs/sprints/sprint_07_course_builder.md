# Rapport de Validation — SPRINT 07 : COURSE BUILDER

## 1. Objectif du Sprint
Transformer le contenu documentaire analysé en véritable cours interactif structuré et pédagogique :
- **Modèles de Données** :
  - `Course` : organisation, document, titre, description, langue, niveau (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`, `EXPERT`), statut (`DRAFT`, `PUBLISHED`, `ARCHIVED`), créateur.
  - `CourseSection` : relation récursive `parent` matérialisant la structure arborescente :
    - `parent is None` -> **Chapitre** (Niveau 1)
    - `parent is Chapitre` -> **Section** (Niveau 2)
    - `parent is Section` -> **Leçon** (Niveau 3) avec `content`, `summary`, `objectives`, `estimated_minutes`.
- **Règle Fondamentale sur le Contenu IA** :
  - Le contenu pédagogique généré par l'IA n'est **jamais considéré comme immuable**.
  - Les enseignants ont un contrôle absolu pour éditer, restructurer, corriger ou enrichir les leçons via `PATCH /sections/{id}/` et l'interface `LessonEditor`.
- **Génération IA RAG & CourseBuilderService** :
  - `POST /courses/{id}/generate` transforme les documents analysés et chunks vectoriels en parcours complet hiérarchisé.
- **Sécurité & Permissions Multi-Tenant** :
  - Isolation stricte des cours par organisation.
  - Seuls les rôles `OWNER`, `ADMIN`, `TEACHER` et le créateur du cours peuvent créer, modifier, supprimer ou générer du contenu de cours.
  - Les étudiants (`STUDENT`) bénéficient d'un accès en lecture pour l'apprentissage.
- **Frontend Next.js** :
  - Pages : `/courses`, `/courses/[id]`, `/courses/[id]/edit`, `/courses/[id]/learn`.
  - Composants : `CourseSidebar`, `CourseOutline`, `LessonViewer`, `LessonEditor`, `CourseProgress`.

---

## 2. Fichiers Créés et Modifiés

### Backend (Django REST Framework)
1. `apps/api/apps/courses/models.py` : Modèles `Course` et `CourseSection` avec hiérarchie récursive `parent`.
2. `apps/api/apps/courses/migrations/0001_initial.py` : Migration initiale pour les tables de cours et sections.
3. `apps/api/apps/courses/permissions.py` : Classes `IsCourseOrganizationMember` et `CanManageCourse` (contrôle RBAC).
4. `apps/api/apps/courses/serializers.py` : Schémas `CourseListSerializer`, `CourseDetailSerializer`, `CourseSectionTreeSerializer`, `CourseCreateSerializer`, `CourseUpdateSerializer`, `CourseSectionSerializer`, `CourseSectionUpdateSerializer`, `CourseGenerateRequestSerializer`.
5. `apps/api/apps/courses/services/builder.py` : `CourseBuilderService` orchestrant la transformation RAG du document en arborescence de cours.
6. `apps/api/apps/courses/services/__init__.py` : Export des services de cours.
7. `apps/api/apps/courses/views.py` : Vues d'API CRUD pour les cours, sections et la génération IA.
8. `apps/api/apps/courses/urls.py` : Routes pour `/courses/`.
9. `apps/api/apps/courses/section_urls.py` : Routes pour `/sections/{id}/`.
10. `apps/api/apps/courses/admin.py` : Enregistrement de `Course` et `CourseSection` dans l'interface d'administration Django.
11. `apps/api/config/urls.py` : Enregistrement des routes `/api/v1/courses/` et `/api/v1/sections/`.
12. `apps/api/tests/test_courses.py` : Suite complète de 10 tests unitaires, d'arborescence, de permissions et de génération IA.

### Frontend (Next.js 14 / TypeScript)
1. `apps/web/types/course.ts` : Typages TypeScript pour `CourseItem`, `CourseSectionItem`, payloads de création et mise à jour.
2. `apps/web/services/courseService.ts` : Client frontend pour tous les endpoints cours et sections.
3. `apps/web/features/course/CourseProgress.tsx` : Composant de suivi de progression (pourcentage, leçons terminées, temps restant).
4. `apps/web/features/course/CourseSidebar.tsx` : Sommaire latéral interactif et dépliable pour la vue apprenant.
5. `apps/web/features/course/CourseOutline.tsx` : Sommaire arborescent complet du cours (Chapitres -> Sections -> Leçons).
6. `apps/web/features/course/LessonViewer.tsx` : Vue de lecture immersive d'une leçon avec objectifs pédagogiques et navigation séquentielle.
7. `apps/web/features/course/LessonEditor.tsx` : Éditeur de leçon dédié aux enseignants pour modifier librement le contenu IA (titre, texte markdown, synthèse, objectifs, durée).
8. `apps/web/features/course/index.ts` : Export central des composants de cours.
9. `apps/web/app/courses/page.tsx` : Page principale de listing et de création de cours.
10. `apps/web/app/courses/[id]/page.tsx` : Page d'aperçu d'un cours avec sommaire et métadonnées.
11. `apps/web/app/courses/[id]/edit/page.tsx` : Page d'édition de cours pour les enseignants.
12. `apps/web/app/courses/[id]/learn/page.tsx` : Page d'apprentissage interactive avec sommaire et lecteur de leçons.
13. `apps/web/components/layout/Navbar.tsx` : Ajout du lien de navigation « Cours ».

### Documentation
1. `docs/api/endpoints_v1.md` : Documentation des endpoints `/api/v1/courses/` et `/api/v1/sections/`.
2. `docs/sprints/sprint_07_course_builder.md` : Présent rapport de validation.

---

## 3. Endpoints Implémentés & Testés

| Méthode | Endpoint | Protection | Description |
|---|---|---|---|
| `GET` | `/api/v1/courses/` | **Bearer JWT** (Membres) | Lister les cours de l'organisation de l'utilisateur |
| `POST` | `/api/v1/courses/` | **Bearer JWT** (Enseignants/Admins) | Créer un nouveau cours |
| `GET` | `/api/v1/courses/{id}/` | **Bearer JWT** (Membres) | Détail d'un cours avec son arborescence complète |
| `PATCH` | `/api/v1/courses/{id}/` | **Bearer JWT** (Enseignants/Admins) | Mettre à jour les métadonnées d'un cours |
| `DELETE` | `/api/v1/courses/{id}/` | **Bearer JWT** (Enseignants/Admins) | Supprimer un cours |
| `GET` | `/api/v1/courses/{id}/sections/` | **Bearer JWT** (Membres) | Lister les chapitres racines et leurs sous-sections |
| `POST` | `/api/v1/courses/{id}/sections/` | **Bearer JWT** (Enseignants/Admins) | Ajouter un chapitre, une sous-section ou une leçon |
| `GET` | `/api/v1/sections/{id}/` | **Bearer JWT** (Membres) | Consulter une leçon individuelle |
| `PATCH` | `/api/v1/sections/{id}/` | **Bearer JWT** (Enseignants/Admins) | **Éditer le contenu didactique IA**, résumé, objectifs |
| `DELETE` | `/api/v1/sections/{id}/` | **Bearer JWT** (Enseignants/Admins) | Supprimer une section ou leçon |
| `POST` | `/api/v1/courses/{id}/generate/` | **Bearer JWT** (Enseignants/Admins) | Générer automatiquement l'arborescence à partir d'un document RAG |

---

## 4. Résultats des Tests et Validations

| Suite de tests / Contrôle | Commande | Résultat | Statut |
|---|---|---|---|
| **CRUD & Permissions Cours** | `pytest test_courses.py::TestCourseCRUDAndPermissions` | 5/5 tests passés (création enseignant, rejet étudiant 403, isolation multi-tenant, patch/delete) | ✅ Validé |
| **Hiérarchie & Édition Leçon** | `pytest test_courses.py::TestCourseSectionHierarchy` | 3/3 tests passés (Chapitre -> Section -> Leçon, édition du contenu IA, rejet parent d'un autre cours) | ✅ Validé |
| **Génération IA Pédagogique** | `pytest test_courses.py::TestAICourseGeneration` | 2/2 tests passés (matérialisation automatique, verrouillage étudiant 403) | ✅ Validé |
| **Total Tests Backend Monorepo** | `pytest apps/api` | **101/101 tests passés** en 3.18s | ✅ Validé |
| **Linter Python** | `ruff check apps/api` | `All checks passed!` | ✅ Validé |
| **Formatage Python** | `ruff format --check apps/api` | 143 files already formatted | ✅ Validé |
| **Typage Frontend Next.js** | `npm run typecheck` | 0 erreur TypeScript (`tsc --noEmit`) | ✅ Validé |

---

## 5. Respect des Règles Métier

1. **Hiérarchie Préservée** : `Course` -> `Chapter` -> `Section` -> `Lesson` modélisée proprement par la relation auto-référentielle `CourseSection.parent`.
2. **Contenu IA Modifiable** : Le contenu généré n'est en aucun cas figé ; un professeur peut le modifier immédiatement via l'API ou l'interface `LessonEditor`.
3. **Cloisonnement Multi-Tenant & Rôles** : Respect strict du cloisonnement par organisation et vérification des rôles (`OWNER`, `ADMIN`, `TEACHER`).
