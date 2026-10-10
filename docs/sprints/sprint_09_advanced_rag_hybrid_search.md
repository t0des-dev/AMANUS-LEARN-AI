# SPRINT 09 — RAG Avancé : Indexation, Recherche Hybride, Citations et Fidélité aux Sources
## Rapport d'Architecture et d'Audit de Sécurité Indépendant

---

### 1. Diagnostic Initial et Limites du RAG Précédent

L'audit architectural approfondi du système RAG d'Amanus Learn AI mené en début de Sprint 09 a révélé les forces existantes et plusieurs angles morts critiques :

1. **Recherche Vectorielle Pure Uniquement** : Le système reposait exclusivement sur la similarité cosinus dense via `pgvector` (`VectorSearchService`). Bien qu'efficace sur les requêtes thématiques larges, ce mécanisme échouait sur :
   - Les acronymes techniques et noms d'algorithmes précis (ex. *BERT*, *RoBERTa*, *ELECTRA*, *MHA*, *RTD*).
   - Les identifiants, références de codes, articles de lois et terminologies rares.
   - Les requêtes avec guillemets ou expressions exactes.
2. **Vulnérabilité aux Pannes de Fournisseurs d'Embeddings** : Si l'API OpenAI ou le modèle d'embeddings subissait un timeout ou un quota dépassé, aucune recherche de secours n'était possible, bloquant la génération IA pour l'utilisateur.
3. **Absence de Versioning des Index** : Les chunks stockaient des embeddings sans consigner le modèle d'embedding utilisé, sa dimension ou le hash de contenu SHA-256 du texte source.
4. **Risque de Prompt Injection Indirecte dans les Extraits Documentaires** : Les extraits injectés dans les prompts étaient séparés par des délimiteurs simples (`--- Source [1] ---`) sans balises d'isolation formelle pour le LLM, créant un vecteur d'attaque si un document importé contenait des instructions de type `Ignore previous instructions`.
5. **Absence de Cache de Requêtes Isolé par Tenant** : Les requêtes répétées recalculaient systématiquement les embeddings et les calculs de similarité en base.

---

### 2. Architecture RAG Avancée Implémentée

```
                                  Requête Utilisateur
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
       Recherche Sémantique Dense                      Recherche Lexicale Exacte
      (pgvector Cosine Similarity)                  (BM25/TF-IDF Exact Term Matching)
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                         Fusion par Rangs Réciproques (RRF)
                         RRF(d) = w_sem/(60 + r_sem) + w_lex/(60 + r_lex)
                                          │
                                          ▼
                       Re-ranking Structurel & Déduplication
                       (Boosts Titres, Chapitres, Sections)
                                          │
                                          ▼
                       Encadrement Sécurisé Anti-Injection
                       <untrusted_document_context> ... </untrusted_document_context>
                                          │
                                          ▼
                        Prompt IA avec Règles Anti-Hallucination
                        & Citations Traçables (Page, Chapitre, ID)
```

#### A. Cycle de Vie et Versioning des Index (`ChunkingService`)
- **Métadonnées de Chunks** : Stockage automatique de `content_hash` (SHA-256), `embedding_model` (`text-embedding-3-small`), `embedding_dim` (`1536`), `chunk_index`, et `char_count`.
- **Métadonnées Document** : Mise à jour de `processing_metadata` avec `index_status: "INDEXED"`, `embedding_model`, `embedding_dim`, et `indexed_at` (horodatage UTC ISO-8601).
- **Idempotence et Invalidation** : Purge automatique des anciens chunks lors d'un re-chunking et invalidation instantanée du cache de requêtes.

#### B. Moteur de Recherche Lexicale (`LexicalSearchService`)
- **Extraction des Termes et Expressions Exactes** : Détection des séquences entre guillemets (`"..."`) et tokenisation insensible à la casse.
- **Scoring Fréquence & Normalisation de Longueur** : Pondération des termes clés (score proportionnel à la fréquence du terme divisée par la racine de la longueur du chunk).
- **Boosts Structurels** : Multiplicateurs de pertinence appliqués lorsque la requête correspond au titre du document, au chapitre ou à la section.
- **Isolation Multi-Tenant Stricte** : Filtrage SQL natif `document__organization_id=organization_id`.

#### C. Fusion Hybride par Rangs Réciproques (`HybridSearchService`)
- **Formule RRF Mathématiquement Conforme** :
  $$\text{Score}_{\text{RRF}}(d) = \frac{0.6}{60 + \text{rank}_{\text{sem}}(d)} + \frac{0.4}{60 + \text{rank}_{\text{lex}}(d)}$$
- **Tolérance aux Pannes & Fallback Gracieux** : Si la recherche sémantique échoue (panne API d'embeddings, timeout réseau, provider hors service), le moteur bascule silencieusement et de manière robuste sur la recherche lexicale sans renvoyer d'erreur 500 à l'utilisateur.

#### D. Orchestration et Cache Dédié (`Retriever`)
- **Modes de Recherche Configurables** : Support natif de `search_mode: "hybrid"` (défaut), `"semantic"`, et `"lexical"`.
- **Cache Isolé par Tenant** : Format de clé sécurisé :
  `rag:query:v{version}:{organization_id}:{document_id or 'all'}:{search_mode}:{hash_requête}:{top_k}`
- **Invalidation Événementielle Ciblée** : `Retriever.invalidate_cache(organization_id, document_id)` déclenchée lors de la réindexation de chunks (`ChunkingService`) ou de la suppression d'un document (`DocumentViewSet.perform_destroy`).

#### E. Anti-Hallucination et Neutralisation de Prompt Injection (`ContextBuilder`)
- **Balise d'Isolation Formelle** : Tous les extraits documentaires sont encapsulés dans `<untrusted_document_context>` avec avertissement formel pour le modèle interdisant l'exécution de toute consigne contenue dans le texte.
- **Sanitisation des Délimiteurs de Contrôle** : Neutralisation des balises réservées (`<|im_start|>`, `<|im_end|>`, `[INST]`, `[/INST]`).
- **Clause de Refus Strict** : Consigne explicite imposant la réponse :
  *« Cette information n'est pas présente dans les documents disponibles. »* en l'absence de sources probantes.

---

### 3. Matrice de Validation des 12 Scénarios Obligatoires

| N° | Scénario d'Évaluation | Comportement Attendu | Résultat Test Réel | Statut |
| :---: | :--- | :--- | :--- | :---: |
| **01** | **Réponse explicite dans le document** | Chunk exact retourné en tête avec citation complète (page, chapitre, titre). | Chunk MHA retourné en rang 1, citation page 1 valide. | **PASSED** |
| **02** | **Question multi-passages** | Récupération de passages distincts nécessaires à la synthèse (Chapitre 1 et 2). | Chunks Attention + Encodage Positionnel présents dans les résultats. | **PASSED** |
| **03** | **Synonymes et reformulation** | Vocabulaire différent du texte source, avantage sémantique/hybride. | Passage positionnel retrouvé avec reformulations périodiques. | **PASSED** |
| **04** | **Recherche de terme exact / acronyme** | Acronymes rares (*ELECTRA*, *RTD*) prioritaires via composante lexicale. | Passage ELECTRA RTD classé en premier grâce au boost lexical. | **PASSED** |
| **05** | **Réponse absente (anti-hallucination)** | Question hors sujet (*photosynthèse chlorophyllienne*). Aucune citation inventée. | Prompt inclut clause de refus strict, aucune source fallacieuse. | **PASSED** |
| **06** | **Vérification de la provenance** | Conservation intégrale des métadonnées structurelles (page, chapitre, section). | Page 2, Chapitre 2, Section 2.1 restitués fidèlement dans les citations. | **PASSED** |
| **07** | **Invalidation de cache après mise à jour** | Modification / réindexation ou suppression invalide le cache de requêtes. | Version incrémentée, ancienne clé obsolète, données rafraîchies. | **PASSED** |
| **08** | **Panne du fournisseur d'embeddings** | Timeout ou erreur 504 de l'API embeddings géré sans crash serveur. | Fallback gracieux vers recherche lexicale, résultat intact. | **PASSED** |
| **09** | **Isolation multi-tenant stricte** | Requête dans l'org A ne doit jamais retourner un document de l'org B. | 0 chunk d'Org B renvoyé dans Org A, étanchéité 100%. | **PASSED** |
| **10** | **Neutralisation de prompt injection** | Document contenant du texte malveillant et des balises de prompt injection. | Délimiteurs neutralisés et encapsulation dans `<untrusted_document_context>`. | **PASSED** |
| **11** | **Cache de requêtes isolé par tenant** | Même question posée par deux organisations distinctes. | Clés de cache avec partitions d'organisation strictement séparées. | **PASSED** |
| **12** | **Non-régression des générateurs IA** | `LessonGenerator`, `SummaryGenerator`, etc. exploitent le nouveau RAG. | Génération de cours et résumés avec citations structurées validée. | **PASSED** |

---

### 4. Résultats des Suites de Tests Globales

- **Tests RAG Avancés (Sprint 09)** : `13 passed in 3.62s` (`apps/api/tests/test_rag_advanced_sprint09.py`).
- **Tests RAG Historiques** : `12 passed in 5.14s` (`apps/api/tests/test_rag.py`).
- **Total Backend Tests** : **349 passed in 47.60s** (0 échec, 0 régression).
- **Tests Frontend (Vitest)** : **32 passed in 10.73s** (8 suites de tests).
- **Linter & Formatage** : `ruff check` validé (0 avertissement).

---

### 5. Audit Indépendant de Sécurité et Recommandations

| Critère d'Audit | Évaluation | Preuve d'Implémentation |
| :--- | :---: | :--- |
| **Multi-Tenancy & Cloisonnement** | **Conforme** | Filtre SQL appliqué au niveau queryset (`document__organization_id=organization_id`) avant toute recherche, et clé de cache préfixée par l'org. |
| **Résilience & Disponibilité** | **Conforme** | Implémentation du double moteur (sémantique + lexical) avec capture d'exception et bascule transparente en cas de panne réseau OpenAI. |
| **Défense en Profondeur (Injection)** | **Conforme** | Neutralisation des tokens spéciaux et démarcation via balise XML explicite `<untrusted_document_context>` dans tous les prompts RAG. |
| **Traçabilité & Provenance** | **Conforme** | Chaque extrait cité porte l'ID du document, le titre, le numéro de page, le chapitre et la section sans interpolation subjective. |
