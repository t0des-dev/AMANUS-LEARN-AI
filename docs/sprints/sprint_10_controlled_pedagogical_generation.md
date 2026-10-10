# SPRINT 10 — Génération Pédagogique Contrôlée et Cohérence Entre les Formats
## Rapport d'Architecture et d'Audit Pédagogique Indépendant

---

### 1. Diagnostic Initial et Enjeux de Cohérence Pédagogique

Avant le Sprint 10, le système de génération d'Amanus Learn AI disposait de générateurs spécialisés pour chaque format (résumés, leçons de cours, diapositives, audio et QCM). Cependant, chaque générateur fonctionnait de façon cloisonnée, introduisant plusieurs failles pédagogiques majeures :

1. **Absence de Représentation Pivot Commune** : Un document source donné pouvait générer un cours mettant l'accent sur certaines notions, tandis que le quiz portait sur des détails marginaux non couverts par la leçon, et les diapositives survolant une terminologie discordante.
2. **Confusion entre Faits Sources et Analogies Pédagogiques** : Les modèles de génération enrichissaient parfois le contenu d'analogies ou d'exemples sans distinguer formellement les faits textuels issus du document des illustrations ajoutées par l'IA.
3. **Absence de Multi-Résolution pour les Résumés** : Les résumés étaient générés selon un gabarit unique rigide, incapable de fournir un mémo ultra-court (100 mots, 3 points essentiels) ou une décomposition analytique détaillée par chapitre.
4. **Risque d'Hallucination dans les QCM sur Documents Courts** : Lorsqu'un utilisateur demandait 10 questions sur un document très court (ex. mémo de 200 mots), le système forçait la génération au risque d'inventer des faits inexistants plutôt que d'émettre des avertissements et d'ajuster le quota.
5. **Inadéquation du Canal Audio** : Les scripts audio héritaient de mentions visuelles inadaptées à l'écoute (« voir figure ci-dessus », « le tableau ci-contre ») et lisaient des syntaxes markdown de tableaux bruts avec des barres verticales.
6. **Absence de Validation Automatisée de la Cohérence Inter-Formats** : Aucun mécanisme ne vérifiait systématiquement que le vocabulaire, les concepts clés et les objectifs restaient parfaitement alignés entre le cours, les slides, le résumé et le quiz.

---

### 2. Architecture de la Génération Pédagogique Contrôlée

```
                                  Document Source Analysé
                                            │
                                            ▼
                           Base Pédagogique Commune (Blueprint)
                             Version Schema: blueprint-v1.0
                  ┌─────────────────────────┴─────────────────────────┐
                  ▼                                                   ▼
       Extraction IA Maîtrisée                             Dérivation Déterministe
      (Faits Sources vs Exemples)                         (depuis Course Validé)
                  │                                                   │
                  └─────────────────────────┬─────────────────────────┘
                                            │
                         Pivot Canonique (PedagogicalBlueprint)
                      - Objectifs Pédagogiques (Taxonomie de Bloom)
                      - Concepts Clés & Définitions Canoniques
                      - Découpage Séquentiel (Sections / Chapitres)
                      - Citations & Références Documentaires [x]
                                            │
          ┌─────────────────┬───────────────┴───────────────┬─────────────────┐
          ▼                 ▼                               ▼                 ▼
    Résumés Multi-      Cours & Leçons                 Quiz / QCM        Présentations & Audio
       Niveaux          (CourseLevel)               Grounded & Bloom      (Adaptation Canal)
   very_short (100w)   Faits vs Exemples            Warnings si court     Sans repère visuel
   synthetic (2-3p)    Citations [x]                Bloom Alignement      Tables transcrites
   detailed (par ch.)
          │                 │                               │                 │
          └─────────────────┴───────────────┬───────────────┴─────────────────┘
                                            │
                                            ▼
                           PedagogicalConsistencyValidator
                         - Couverture conceptuelle vérifiée
                         - Absence de références visuelles en audio
                         - Alignement objectifs / questions de quiz
                         - Remédiation Biphasée Bornée (max_retries <= 1)
```

---

### 3. Composants et Implémentation Détaillée

#### A. Schéma Pivot et Base Pédagogique Commune (`PedagogicalBlueprint`)
- **Versionnement du Schéma** : `version: "blueprint-v1.0"`.
- **Entités Dataclass Normalisées** :
  - `LearningObjective` : identifiant unique, niveau taxonomique de Bloom (`Comprendre`, `Appliquer`, `Analyser`, `Évaluer`), formulation mesurable par verbe d'action, provenance source `[x]`.
  - `KeyConcept` : terme canonique, définition précise tirée du document, statut d'importance (`CORE` ou `SECONDARY`), référence source.
  - `SectionOutline` : découpage séquentiel clair séparant explicitement les `source_facts` (faits avérés du document) des `pedagogical_examples` (illustrations pédagogiques).
- **Service d'Orchestration & Réutilisation Déterministe** :
  `PedagogicalBlueprintService.derive_from_course(course)` : permet de reconstruire instantanément et sans coût LLM un blueprint complet à partir d'un cours existant validé par un enseignant.

#### B. Résumés Multi-Niveaux (`SummaryGenerator` & `PromptService`)
- **Niveau `very_short`** : Limité à 1 paragraphe d'environ 100 mots, exactement 3 points essentiels (`key_takeaways`) prioritaires pour une révision flash.
- **Niveau `synthetic`** : Vue d'ensemble équilibrée en 2-3 paragraphes avec synthèse par chapitre et citations sources `[x]`. Conserve l'identifiant de version canonique `summary-v1.0`.
- **Niveau `detailed`** : Analyse approfondie chapitre par chapitre, explicitant les relations entre concepts, les définitions majeures et les limites/conditions de validité mentionnées dans les sources.
- **Exposition Complète** : Intégré de bout en bout dans l'API (`SummaryGenerationSerializer`, `GenerationService`, `AIService`, et `generate_summary` view).

#### C. Quiz Groundés et Gestion des Sources Restreintes (`QuizGeneratorService`)
- **Alignement sur les Objectifs** : Injection automatique des objectifs d'apprentissage et concepts clés du blueprint dans le prompt de génération de questions.
- **Contrôle de Richesse Documentaire & Dégradation Gracieuse** :
  - Détection automatique des documents courts (`total_source_chars < 600`).
  - Émission explicite d'avertissements (`warnings`) lorsque la densité documentaire est insuffisante pour honorer le nombre demandé de questions, au lieu d'extrapoler ou d'inventer des faits.
  - Préservation intégrale des questions validées avec attribution d'une liste `QuestionList` enrichie de métadonnées d'avertissement.
- **Validation Stricte QCM** :
  - Proscription des méta-distracteurs (« Toutes les réponses », « Aucune des réponses »).
  - Rejet des explications tautologiques (« C'est la bonne réponse »).
  - Exactement 4 options de longueur homogène avec une seule bonne réponse non ambiguë.

#### D. Adaptation du Canal Audio (`PedagogicalScriptGenerator`)
- **Suppression des Références Visuelles** : Filtrage multilingue (FR, AR, EN) éliminant automatiquement les formulations inadaptées à l'écoute :
  * « voir ci-dessus », « voir ci-dessous », « comme illustré », « le tableau ci-contre », « dans le schéma ci-dessous ».
  * « see above », « as shown above », « see figure », « in the table below ».
  * « انظر أعلاه », « كما هو موضح », « راجع الجدول ».
- **Reformulation des Tableaux Markdown** : Détection des syntaxes `| col1 | col2 |` et conversion en narration fluide parlée (« Notons les correspondances suivantes : ... ») sans lecture des caractères de séparation `|`.

#### E. Validateur de Cohérence Inter-Formats (`PedagogicalConsistencyValidator`)
- **Contrôles Automatisés** :
  - `validate_course_and_summary_alignment` : vérifie la couverture conceptuelle et la conformité du volume selon le niveau du résumé.
  - `validate_course_and_quiz_alignment` : vérifie que les questions évaluent les concepts du cours sans hors-sujet.
  - `validate_course_and_slides_alignment` : valide la correspondance des sections et alerte en cas de surcharge textuelle (> 8 puces par diapositive).
  - `validate_course_and_audio_alignment` : contrôle l'absence absolue de repères visuels et de tables brutes.
- **Remédiation Biphasée Bornée** :
  `remediate_with_bounded_retry(generator_fn, validator_fn, max_retries=1)` : garantit qu'en cas d'incohérence détectée, une seule tentative de remédiation est exécutée, protégeant l'infrastructure contre les boucles infinies et la surconsommation de crédits/quotas.

---

### 4. Résultats des Tests et Audit de Non-Régression

| Domaine / Composant | Tests Dédiés | Statut | Résultat |
| :--- | :--- | :--- | :--- |
| **Pedagogical Blueprint Schema** | `TestPedagogicalBlueprint` (3 tests) | PASS | Validation et sérialisation blueprint-v1.0 conformes |
| **Dérivation Déterministe** | `test_derive_blueprint_from_course_without_extra_llm` | PASS | Reconstruction sans appel LLM supplémentaire |
| **Résumés Multi-Niveaux** | `TestMultiLevelSummaryGeneration` (2 tests) | PASS | Prompts et flux very_short / synthetic / detailed |
| **Quiz Alignés & Warnings** | `TestQuizPedagogicalAlignmentAndWarnings` (2 tests) | PASS | Détection sources courtes et rejet méta-distracteurs |
| **Adaptation Audio** | `TestAudioScriptSpeechAdaptation` (2 tests) | PASS | Cures visuelles supprimées et tableaux reformulés |
| **Cohérence Inter-Formats** | `TestPedagogicalConsistencyValidator` (5 tests) | PASS | Contrôles cross-modal et remédiation bornée (max=1) |
| **Suite Backend Complète** | **364 tests pytest** | **100% PASS** | **364 passed en 42.82s (0 échec, 0 régression)** |
| **Suite Frontend Complète** | **32 tests Vitest** | **100% PASS** | **32 passed (8 fichiers de composants)** |
| **Qualité & Linting** | `ruff check apps/api` | **100% PASS** | **All checks passed (0 erreur, 0 avertissement)** |
