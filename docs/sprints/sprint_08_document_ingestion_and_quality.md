# SPRINT 08 — Robustesse de l'Ingestion Documentaire, Extraction et Contrôle Qualité
## Rapport d'Architecture et d'Audit de Sécurité Indépendant

---

### 1. Diagnostic Initial et Parcours Réel d'Ingestion

L'audit architectural préalable du pipeline d'ingestion documentaire d'Amanus Learn AI a permis d'établir la cartographie complète du flux :

```
Upload (MultiPart) ➔ Validation Binaire & Archive ➔ Stockage S3/Local ➔ Tâche Celery (queue 'heavy')
                                                                               │
       ┌───────────────────────────────────────────────────────────────────────┘
       ▼
Détection & Parsing (PDF/DOCX/PPTX/TXT) ➔ Évaluation Qualité (DocumentQualityEvaluator)
       │                                            │
       ├─ Échec / Corrompu ➔ Status: FAILED         ├─ Grade FULL ➔ READY + Chunks + Vector Embeddings
       └─ Format Invalide ➔ Rejet HTTP 400          ├─ Grade PARTIAL ➔ READY + Chunks + Quality Warnings
                                                    └─ Grade UNUSABLE ➔ READY / FAILED + 0 Chunks + Warning Flag
```

#### Capacités et Bibliothèques Réellement Installées
- **PDF** : `pypdf` (`PdfReader`, extraction de texte, détection de flux d'images). Fallback OCR gracieux via `OCRParser` (détection `pytesseract` / binaire Tesseract).
- **DOCX** : `python-docx` (`docx.Document`, extraction hiérarchique H1/H2/H3, listes à puces, paragraphes et tableaux).
- **PPTX** : `python-pptx` (`pptx.Presentation`, extraction diapositive par diapositive, titres, formes de texte, tableaux et notes de présentation).
- **TXT** : Décodage UTF-8 natif avec normalisation Unicode NFKC.
- **Stockage** : `LocalStorageService` / `S3StorageService` (MinIO/AWS S3).
- **Orchestration Asynchrone** : Celery, queue `"heavy"`, tâches `process_document`, `extract_document`, `create_chunks`.

---

### 2. Vulnérabilités Identifiées et Protections Apportées

| Risque / Vulnérabilité | Gravité | Composant Concerné | Solution Apportée |
| :--- | :--- | :--- | :--- |
| **Faux Positifs sur Documents Vides** | Critique | `ingestion/tasks.py` | Avant le Sprint 08, un document de 0 caractère était marqué `READY`. Intégration de `DocumentQualityEvaluator` qui classe en `UNUSABLE`, refuse la création de faux chunks et émet un avertissement explicite. |
| **Traversée de Répertoire & Noms Dangereux** | Majeur | `documents/validators.py`, `serializers.py` | Ajout de `sanitize_file_name` extrayant le nom de base, supprimant les `..`, séparateurs et caractères de contrôle pour le stockage et la base de données. |
| **Zip Bombs & Décompression Malveillante** | Majeur | `documents/validators.py` | Inspection des archives DOCX/PPTX avec vérification du ratio de décompression (seuil max 50x) et du volume total décompressé (max 150 Mo). |
| **Macros et Composants Actifs Exécutables** | Majeur | `documents/validators.py` | Rejet formel des archives contenant `vbaProject.bin`, exécutables, `.vbs`, `.sh`, `.bat`. |
| **Concurrence & Traitements Répétés** | Majeur | `documents/views.py` | Protection contre le déclenchement concurrent : renvoi d'un code HTTP 409 Conflict si le document est déjà au statut `EXTRACTING`, `PROCESSING`, `CHUNKING`. |
| **Déni de Service Mémoire sur Gros Fichiers** | Majeur | `ingestion/parsers/` | Plafonds stricts : `MAX_EXTRACT_PAGES = 500` pour PDF, `MAX_EXTRACT_SLIDES = 200` pour PPTX, et `MAX_EXTRACT_CHARS = 1_000_000`. Avertissements `MAX_PAGES_LIMIT_REACHED` émis en cas de dépassement. |
| **Silence sur Pages Scannées sans OCR** | Moyen | `ingestion/parsers/pdf_parser.py` | Détection explicite des pages images avec moins de 20 caractères et émission de l'avertissement `PAGE_X_SCANNED_NEEDS_OCR` plutôt que de prétendre que le document est complet. |

---

### 3. Niveaux de Qualité et Métadonnées

Le service `DocumentQualityEvaluator` introduit 3 grades d'exploitation :
1. **`FULL`** : Densité textuelle saine, aucune anomalie bloquante.
2. **`PARTIAL`** : Présence de pages scannées sans moteur OCR, de diapositives blanches ou d'erreurs locales n'empêchant pas l'exploitation du reste du document.
3. **`UNUSABLE`** : Document vide, répétitions dégénératives massives ou volume de texte inférieur au seuil minimal (30 caractères).

Les métadonnées enrichies (`processing_metadata`) contiennent :
- `quality_grade` : `"FULL" | "PARTIAL" | "UNUSABLE"`
- `quality_warnings` : liste des alertes générées (`DOCUMENT_EMPTY_OR_UNUSABLE`, `SCANNED_PAGES_DETECTED_X`, `MAX_PAGES_LIMIT_REACHED`, etc.)
- `total_chars`, `total_pages`, `empty_pages`, `scanned_pages`
- `processed_at` : timestamp ISO UTC traçable

---

### 4. Résultats des Tests de Validation (10/10)

La suite de tests automatisés [`apps/api/tests/test_ingestion_robustness_sprint08.py`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/api/tests/test_ingestion_robustness_sprint08.py) valide l'intégralité des 10 exigences prescrites :

1. `test_1_pdf_with_usable_text` : **PASSED** (Grade `FULL`, chunks et pages indexés).
2. `test_2_empty_or_near_empty_document` : **PASSED** (Rejet upload 0 octet + grade `UNUSABLE` sur contenu vide).
3. `test_3_corrupted_or_invalid_file` : **PASSED** (Statut `FAILED` avec message explicite sans crash).
4. `test_4_unsupported_format` : **PASSED** (Rejet HTTP 400 sur formats non autorisés).
5. `test_5_size_limit_or_budget_exceeded` : **PASSED** (Blocage à l'upload lors du dépassement du plafond configuré).
6. `test_6_partial_extraction_with_warnings` : **PASSED** (Grade `PARTIAL` et conservation des avertissements).
7. `test_7_permission_and_cross_tenant_isolation` : **PASSED** (Isolation stricte des lectures, pages, lancements et suppressions).
8. `test_8_boundary_preservation_pages_and_slides` : **PASSED** (Préservation des titres, diapositives et notes de présentation PPTX).
9. `test_9_concurrency_and_duplicate_processing_guard` : **PASSED** (HTTP 409 Conflict sur requêtes répétées en vol).
10. `test_10_cascading_deletion_and_derived_data_consistency` : **PASSED** (Suppression en cascade document, pages, chunks et fichier stockage).

**Résultat global de non-régression** : 336/336 tests backend passés, 32/32 tests frontend Vitest passés.

---

### 5. Revue d'Audit Indépendant

1. **Sécurité des fichiers** : Conforme. Validation magic bytes, vérification d'archive zip anti-bombes, rejet des macros VBA, assainissement des chemins.
2. **Isolation des tenants** : Conforme. Toutes les vues (`DocumentListCreateView`, `DocumentDetailView`, `DocumentProcessView`, `DocumentPagesListView`, `DocumentProcessingStatusView`) filtrent par `organization__members__user=request.user`.
3. **Qualité d'extraction** : Conforme. Distingue explicitement succès complet, partiel et document inexploitable.
4. **Fidélité & Frontières** : Conforme. Pages et diapositives numérotées, titres et notes de présentation conservés.
5. **Régression IA** : Conforme. Les générateurs de cours, résumés, quiz et slides s'appuient sur les chunks existants sans rupture de contrat d'interface.
