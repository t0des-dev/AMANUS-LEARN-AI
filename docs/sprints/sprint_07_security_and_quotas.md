# SPRINT 07 — Sécurité, Quotas et Maîtrise des Coûts de Génération IA
## Rapport d'Architecture et d'Audit de Sécurité Indépendant

---

### 1. Architecture de Consommation et Cartographie

Les points d'entrée de génération IA de la plateforme `amanus-learn-ai` ont été audités et rattachés à des politiques de quotas strictes avec traçabilité unitaire :

| Pipeline de Génération | Modèle / Provider | Point d'Entrée API | Traitement | Métrique Suivie | Coût Estimé Unitaire |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cours & Documents** | GPT-4o / Claude 3.5 Sonnet / Mock | `POST /api/v1/courses/{id}/generate/` | Synchrone / Celery default | `ai_generations` | ~$0.015 / run |
| **Slides & Présentations** | Modèle LLM structuré | `POST /api/v1/courses/{id}/presentations/` | Synchrone | `slides` | ~$0.012 / run |
| **Synthèse Vocale (TTS)** | OpenAI TTS-1 / ElevenLabs / Mock | `POST /api/v1/audio/sections/{id}/generate/` | Celery heavy queue | `audio` (minutes) | ~$0.015 / minute |
| **Quiz & Évaluations** | Modèle LLM validation 4Q | `POST /api/v1/quizzes/{id}/generate/` | Synchrone | `quizzes` | ~$0.008 / run |
| **Documents RAG direct** | AIService Facade | `POST /api/v1/documents/{id}/generate/{type}/`| Synchrone | `ai_generations` | ~$0.010 / run |

---

### 2. Vulnérabilités Identifiées et Corrigées

1. **Race Condition sur le Dernier Slot de Quota (Bloquant)** :
   - *Anomalie constatée* : L'ancienne méthode `check_quota` lisait la consommation sans verrouiller la ligne en base (`select_for_update`). Deux requêtes simultanées arrivant alors qu'il restait 1 slot pouvaient franchir la validation et incrémenter la consommation au-delà de la limite souscrite.
   - *Correction* : Mise en place du modèle `QuotaReservation` et de réservations atomiques à 2 phases (`reserve_quota` -> `commit_quota` / `release_quota`). Un verrou exclusif `select_for_update()` agrège les consommations confirmées et les réservations en attente (`PENDING`).
2. **Absence de Quota sur les Points d'Entrée de Génération (Majeur)** :
   - *Anomalie constatée* : Les endpoints de génération de cours, slides, audio et quiz n'appelaient pas le service de quota, permettant des générations illimitées pour n'importe quel plan.
   - *Correction* : Intégration systématique de la réservation préalable de quota dans l'ensemble des 5 contrôleurs de génération. En cas de dépassement, l'API renvoie un code HTTP 429 avec le code métier stable `quota_exceeded`.
3. **Double Comptage lors des Retries Réseau (Majeur)** :
   - *Anomalie constatée* : En cas de timeout côté client, le renvoi d'une même requête pouvait consommer deux fois les crédits de l'organisation.
   - *Correction* : Prise en charge d'un jeton d'idempotence (`idempotency_key`). Si une réservation existe déjà avec cette clé, le service la renvoie sans décrémentation supplémentaire.
4. **Risque de Timeout Fournisseur Incertain (Majeur)** :
   - *Anomalie constatée* : Si une requête vers OpenAI ou ElevenLabs subit un timeout réseau, considérer la requête comme gratuite peut masquer une facturation réelle côté fournisseur.
   - *Correction* : Mise en quarantaine via le statut `TIMEOUT_UNCERTAIN` avec conservation du coût estimé et flag `is_cost_estimated=True` pour réconciliation manuelle ou asynchrone.
5. **Absence de Limitation de Débit Anti-Burst (Majeur)** :
   - *Anomalie constatée* : Vulnérabilité aux attaques de déni de service par rafales de requêtes sur les endpoints IA coûteux.
   - *Correction* : Création des classes DRF `AIGenerationRateThrottle` (30 req/min) et `AIBurstThrottle` (10 req/min) dans `apps/billing/throttling.py`.
6. **Injections de Prompt et Fuites de Clés API dans les Sources (Majeur)** :
   - *Anomalie constatée* : Les documents importés pouvaient contenir des balises spéciales (`<|im_start|>`) ou des tentatives de jailbreak susceptibles de détourner le tuteur IA.
   - *Correction* : Création du service `PromptSecuritySanitizer` dans `apps/ai/services/security.py` masquant les clés d'API (`[REDACTED_SECRET]`), filtrant les caractères de contrôle non imprimables et encapsulant le contexte documentaire dans la balise étanche `<untrusted_document_context>`.

---

### 3. Règles de Quota Implémentées

- **Par Organisation** : Seuils configurés par plan dans `PLAN_QUOTAS` (Free: 10 IA / 20 Slides / 15 min Audio / 10 Quizzes ; Pro: 250 IA / 200 Slides / 180 min Audio ; Enterprise: illimité).
- **Par Utilisateur** : Seuils journaliers configurés dans `USER_DAILY_LIMITS` (ex: max 5 générations/jour pour un étudiant sur plan gratuit, prévenant la monopolisation des ressources de l'organisation).
- **Réservations à Deux Phases** :
  - `reserve_quota(...)` : Réservation atomique (statut `PENDING`) avant l'appel modèle.
  - `commit_quota(...)` : Confirmation et consolidation dans `UsageRecord` après succès.
  - `release_quota(...)` : Remboursement automatique en cas d'erreur ou d'annulation.
  - `mark_timeout_uncertain(...)` : Quarantaine protectrice en cas d'interruption réseau.

---

### 4. Résultats des Tests de Validation (16/16)

La suite de tests automatisés [`apps/api/tests/test_security_quotas_sprint07.py`](file:///c:/Users/PC/Desktop/workflow/amanus-learn-ai/apps/api/tests/test_security_quotas_sprint07.py) valide l'intégralité des 16 scénarios prescrits :

1. `test_authorized_request_when_quota_available` : **PASSED**
2. `test_refusal_when_quota_exhausted` : **PASSED** (HTTP 429 `quota_exceeded`)
3. `test_quota_isolation_between_organizations` : **PASSED**
4. `test_per_user_limitation_when_enabled` : **PASSED**
5. `test_concurrent_reservations_last_quota_slot` : **PASSED**
6. `test_double_counting_prevention_on_retry` : **PASSED**
7. `test_failure_before_provider_call_releases_quota` : **PASSED**
8. `test_timeout_with_uncertain_provider_result` : **PASSED**
9. `test_task_retry_does_not_double_count` : **PASSED**
10. `test_task_cancellation_refunds_quota` : **PASSED**
11. `test_consistency_of_consumption_after_success` : **PASSED**
12. `test_endpoint_protection_against_unauthorized_org` : **PASSED**
13. `test_rate_limiting_burst_protection` : **PASSED**
14. `test_dashboard_access_control` : **PASSED**
15. `test_no_secrets_in_logs_and_sanitized_inputs` : **PASSED**
16. `test_compatibility_with_existing_generators` : **PASSED**

**Bilan global du dépôt** :
- **326 tests backend exécutés** : **326 passés avec succès (0 échec, 0 régression)**.
- **32 tests frontend Vitest exécutés** : **32 passés avec succès**.
- **Typage statique TypeScript (`tsc --noEmit`)** : **0 erreur**.
- **Linter Ruff (`ruff check apps/api`)** : **0 erreur**.
