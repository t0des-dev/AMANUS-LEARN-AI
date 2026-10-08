# SPRINT 11 — SLIDES GENERATOR

## 1. Objectifs & Vue d'ensemble

Le Sprint 11 implémente le générateur de présentations pédagogiques (**Slides Generator**) d'Amanus Learn AI. Ce module transforme un cours complet (`Course`) en une présentation structurée (`Presentation`) composée de diapositives interactives (`PresentationSlide`), offre un studio d'édition et de prévisualisation Web responsive 16:9 dans Next.js, et permet l'exportation au format Microsoft PowerPoint (`.pptx`) via `python-pptx` (de manière synchrone ou asynchrone via Celery).

---

## 2. Architecture & Pipeline

```text
Course (Chapitres & Notions)
  │
  ▼
Slide Planner (Structure pédagogique : Titre, Sommaire, Concepts, Synthèse, Conclusion)
  │
  ▼
Slide Generator (Persistance Presentation & PresentationSlide)
  │
  ▼
Web Studio & Preview Next.js (/presentations/[id])
  │  ├── SlideNavigator (Plan des slides, réordonnancement, ajout, suppression)
  │  ├── SlidePreview (Canevas 16:9 widescreen, thèmes visuels, notes orateur, plein écran)
  │  ├── SlideEditor (Édition des titres, puces didactiques, notes, suggestions visuelles)
  │  └── PresentationToolbar (Renommage, sélection de thème, export)
  │
  ▼
PPTX Export (python-pptx)
  ├── Rendu 16:9 (13.333" x 7.5"), palettes graphiques par thème
  ├── Notes du présentateur (notes_slide)
  └── Persistance dans le service de stockage (LocalStorage / S3 / MinIO)
```

---

## 3. Modèles de Données

### `Presentation`
- `id` : UUID (Clé primaire)
- `course` : ForeignKey vers `Course` (suppression en cascade)
- `title` : CharField (Titre de la présentation)
- `theme` : Choix (`modern_dark`, `minimal_light`, `academic_indigo`, `corporate_blue`)
- `status` : Choix (`DRAFT`, `GENERATING`, `READY`, `EXPORTING`, `FAILED`)
- `storage_key` : CharField (Clé de stockage du fichier PPTX généré)
- `created_at` / `updated_at` : DateTimeField
- Méthode : `get_export_url()` retourne l'URL de téléchargement direct.

### `PresentationSlide`
- `id` : UUID (Clé primaire)
- `presentation` : ForeignKey vers `Presentation`
- `slide_number` : PositiveIntegerField (Ordre séquentiel)
- `title` : CharField (Titre de la slide)
- `content` : TextField (Points clés et puces didactiques)
- `speaker_notes` : TextField (Notes orateur pour le présentateur)
- `image_prompt` : TextField (Prompt d'illustration / idée visuelle)
- `image_url` : URLField (URL de l'image si générée)
- `created_at` / `updated_at` : DateTimeField

---

## 4. Endpoints API

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/api/v1/courses/{id}/presentations/` | Génère une nouvelle présentation à partir d'un cours |
| `GET` | `/api/v1/courses/{id}/presentations/` | Liste les présentations associées à un cours |
| `GET` | `/api/v1/presentations/{id}/` | Détails d'une présentation et de ses slides ordonnées |
| `PATCH` | `/api/v1/presentations/{id}/` | Mise à jour du titre, du thème ou de l'ordre des slides |
| `DELETE` | `/api/v1/presentations/{id}/` | Suppression d'une présentation et de ses slides |
| `POST` | `/api/v1/presentations/{id}/export/` | Exportation au format PPTX (paramètre optionnel `?async=true`) |
| `POST` | `/api/v1/presentations/{id}/slides/` | Ajout d'une nouvelle diapositive |
| `PATCH` | `/api/v1/presentations/{id}/slides/{slide_id}/` | Modification du titre, contenu ou notes d'une slide |
| `DELETE` | `/api/v1/presentations/{id}/slides/{slide_id}/` | Suppression d'une slide avec réindexation séquentielle automatique |
| `POST` | `/api/v1/presentations/{id}/reorder/` | Réordonnancement en bloc des slides |

---

## 5. Composants Next.js

Situés dans `apps/web/components/slides/` et intégrés dans la page `apps/web/app/presentations/[id]/page.tsx` :

1. **`SlideNavigator`** :
   - Vignettes des slides avec badges de numérotation.
   - Boutons Monter ($\uparrow$) et Descendre ($\downarrow$) pour réordonner les slides.
   - Bouton de suppression avec confirmation.
   - Bouton d'ajout immédiat d'une slide.
2. **`SlidePreview`** :
   - Canevas 16:9 widescreen haute fidélité.
   - Gestion des styles selon le thème (`modern_dark`, `minimal_light`, `academic_indigo`, `corporate_blue`).
   - Tiroir dépliable pour les notes de l'orateur.
   - Navigation clavier (Flèches gauche / droite / Espace) et mode plein écran (`F` ou bouton).
3. **`SlideEditor`** :
   - Éditeur du titre de la diapositive.
   - Zone de saisie des points clés / puces didactiques avec bouton d'ajout rapide.
   - Zone pour les notes de l'orateur.
   - Champ pour le prompt d'illustration visuelle.
   - Indicateurs d'état d'enregistrement en direct.
4. **`PresentationToolbar`** :
   - Renommage inline du titre de la présentation.
   - Menu déroulant de sélection du thème visuel.
   - Déclencheur d'export PPTX (avec badge de téléchargement direct une fois prêt).

---

## 6. Export PPTX (`python-pptx`)

- **Format** : Widescreen 16:9 (`slide_width = Inches(13.333)`, `slide_height = Inches(7.5)`).
- **Cartouche & Typographie** : Hiérarchie typographique (32-40pt pour les titres, 18-20pt pour les points clés), boîtes englobantes à coins arrondis.
- **Notes de présentation** : Injectées directement dans `slide.notes_slide.notes_text_frame.text`.
- **Exécution asynchrone** : Tâche Celery `export_presentation_task` (`apps/slides/tasks.py`) pour les jeux de diapositives volumineux.

---

## 7. Tests & Validation

- `SlidePlannerAndGeneratorTests` : Validation de la génération de plans didactiques et de la création des modèles.
- `PPTXExporterTests` : Vérification du ratio 16:9, intégrité du fichier généré avec `python-pptx`, notes orateur et intégration avec le service de stockage.
- `PresentationAPITests` : Couverture complète des routes REST (création, consultation, édition, réordonnancement, suppression, permissions multi-tenant et export synchrone/asynchrone).
- **100% des tests passants** : 17 tests dédiés slides + 139 tests des sprints précédents (156 tests au total).
