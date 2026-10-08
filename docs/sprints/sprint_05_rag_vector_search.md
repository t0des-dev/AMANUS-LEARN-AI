# Rapport de Validation — SPRINT 05 : RAG / VECTOR SEARCH

## 1. Objectif du Sprint
Mettre en œuvre le moteur RAG complet fondé sur PostgreSQL + pgvector, découplé derrière une couche d'abstraction multi-provider et sécurisé par un cloisonnement multi-tenant strict :
- Activation de l'extension `vector` PostgreSQL et intégration avec `DocumentChunk.embedding (1536)`.
- Abstraction `EmbeddingProvider` (implémentations `DeterministicEmbeddingProvider` et `OpenAIEmbeddingProvider`).
- Service de recherche vectorielle `VectorSearchService` (distance cosinus pgvector sur PostgreSQL, calcul vectoriel unitaire sur SQLite).
- Re-classement hybride `Reranker` (pondération vectorielle + pertinence lexicale + boost des titres de chapitre/section).
- Générateur de citations `CitationBuilder` préservant l'intégralité de la provenance (`document_id`, `page`, `chapter`, `section`, `chunk_id`, extrait).
- Constructeur de contexte `ContextBuilder` avec règles strictes anti-hallucination.
- Orchestrateur `Retriever` exécutant le pipeline de bout en bout : `Question -> Embedding -> Vector Search -> Metadata Filter -> Top K -> Re-ranking -> Context -> Sources`.
- Endpoints REST sécurisés : `POST /api/v1/rag/search/` et `POST /api/v1/rag/query/`.
- Tests unitaires et d'isolation multi-tenant stricte (interdiction absolue de fuite de chunks inter-organisations).

---

## 2. Fichiers Créés et Modifiés

### Fichiers Créés
1. `apps/api/apps/ai/services/embeddings/base.py` : Classe de base abstraite `EmbeddingProvider`.
2. `apps/api/apps/ai/services/embeddings/mock_provider.py` : `DeterministicEmbeddingProvider` générant des vecteurs unitaires normalisés 1536D.
3. `apps/api/apps/ai/services/embeddings/openai_provider.py` : Adapter d'embeddings OpenAI avec repli sécurisé.
4. `apps/api/apps/ai/services/embeddings/__init__.py` : Factory `get_embedding_provider()` et gestionnaire de cycle de vie.
5. `apps/api/apps/ai/services/vector_search.py` : `VectorSearchService` avec support pgvector natif et compatibilité SQLite.
6. `apps/api/apps/ai/services/reranker.py` : `Reranker` hybride (sémantique + lexical + boost structurel).
7. `apps/api/apps/ai/services/citation_builder.py` : `CitationBuilder` garantissant la traçabilité complète des sources.
8. `apps/api/apps/ai/services/context_builder.py` : `ContextBuilder` structurant le prompt contextuel avec consignes anti-hallucination.
9. `apps/api/apps/ai/services/retriever.py` : `Retriever` orchestrant le pipeline complet.
10. `apps/api/apps/ai/services/__init__.py` : Exports du package de services RAG.
11. `apps/api/apps/ai/serializers.py` : Schémas `RAGSearchRequestSerializer`, `RAGSearchResultItemSerializer`, `RAGCitationItemSerializer`, `RAGSearchResponseSerializer`, `RAGQueryResponseSerializer`.
12. `apps/api/apps/ai/views.py` : Vues d'API `RAGSearchView` et `RAGQueryView` avec validation multi-tenant.
13. `apps/api/apps/ai/urls.py` : Définition des routes de l'application AI/RAG.
14. `apps/api/tests/test_rag.py` : Suite complète de 12 tests unitaires, de pipeline et d'isolation multi-tenant.
15. `apps/web/types/rag.ts` : Typages TypeScript pour recherche, requêtes et citations RAG.
16. `apps/web/services/ragService.ts` : Client frontend pour `/api/v1/rag/search/` et `/api/v1/rag/query/`.
17. `docs/sprints/sprint_05_rag_vector_search.md` : Présent rapport de validation.

### Fichiers Modifiés
1. `apps/api/apps/ingestion/services/chunking.py` : Calcul et affectation automatique des embeddings lors de la création des chunks.
2. `apps/api/config/urls.py` : Déclaration du préfixe d'URL `/api/v1/rag/`.
3. `docs/api/endpoints_v1.md` : Spécification des routes de recherche et de requêtage RAG.

---

## 3. Endpoints Implémentés & Testés

| Méthode | Endpoint | Protection | Description |
|---|---|---|---|
| `POST` | `/api/v1/rag/search/` | **Bearer JWT** (Membres tenant) | Recherche vectorielle filtrée par `organization_id`, réordonnée par score hybride |
| `POST` | `/api/v1/rag/query/` | **Bearer JWT** (Membres tenant) | Requête RAG avec contexte assemblé, citations et synthèse des sources |

---

## 4. Résultats des Tests et Validations

| Suite de tests / Contrôle | Commande | Résultat | Statut |
|---|---|---|---|
| **Abstractions Embeddings** | `pytest test_rag.py::EmbeddingProviderTests` | 3/3 tests passés (dimension 1536, normalisation L2, similarité sémantique) | ✅ Validé |
| **Contexte & Citations** | `pytest test_rag.py::ContextAndCitationBuilderTests` | 2/2 tests passés (préservation de document, page, chapitre, section, chunk) | ✅ Validé |
| **Re-classement Hybride** | `pytest test_rag.py::RerankerTests` | 1/1 test passé (boost lexical et titres de sections) | ✅ Validé |
| **Isolation Multi-Tenant & API** | `pytest test_rag.py::RAGPipelineAndAPITests` | 6/6 tests passés (rejet 403 inter-tenant, exclusion stricte des chunks tiers, filtre document) | ✅ Validé |
| **Total Tests Backend Monorepo** | `pytest apps/api` | **72/72 tests passés** en 6.67s | ✅ Validé |
| **Linter Python** | `ruff check apps/api` | `All checks passed!` | ✅ Validé |
| **Formatage Python** | `ruff format --check apps/api` | 117 files already formatted | ✅ Validé |
| **Typage Frontend** | `npm run typecheck` | 0 erreur TypeScript (`tsc --noEmit`) | ✅ Validé |

---

## 5. Validation des Critères d'Acceptation

- [x] **PostgreSQL & pgvector** : Intégration active sur `DocumentChunk.embedding` (vecteur 1536D).
- [x] **Services créés** : `EmbeddingProvider`, `VectorSearchService`, `Retriever`, `Reranker`, `ContextBuilder`, `CitationBuilder`.
- [x] **Indépendance IA** : Embeddings abstraits derrière `EmbeddingProvider` sans clés hardcodées.
- [x] **Endpoints créés** : `POST /api/v1/rag/search/` et `POST /api/v1/rag/query/`.
- [x] **Filtrage par organisation** : Contrôle strict, un utilisateur ne peut jamais requêter une autre organisation (403/404).
- [x] **Métadonnées conservées** : Chaque source retient `document_id`, `document_title`, `page`, `chapter`, `section`, `chunk_id` et son extrait.
- [x] **Anti-hallucination** : Règle stricte intégrée dans le prompt RAG.
- [x] **Chatbot final non implémenté** : Réservé aux sprints conversationnels ultérieurs.
- [x] **Arrêt strict au Sprint 05** : Conforme au principe de développement itératif autonome.
