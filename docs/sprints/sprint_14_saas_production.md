# SPRINT 14 — SAAS & PRODUCTION-READY ARCHITECTURE

## 1. Objectif & Vue d'ensemble

Le **Sprint 14** transforme la plateforme **Amanus Learn AI** d'un MVP fonctionnel en une application **SaaS multi-tenant production-ready**, hautement sécurisée, scalable et monitorée.

Ce sprint délivre :
1. **L'architecture de facturation & d'abonnements** multi-plans (`FREE`, `PRO`, `BUSINESS`, `ENTERPRISE`).
2. **Le moteur de quotas et de suivi de consommation en temps réel** (`QuotaService`, `UsageRecord`).
3. **Le système de traçabilité et d'audit légal/sécurité** (`AuditLogService`, `AuditLog`).
4. **Le renforcement complet de la sécurité** (rate limiting, validation MIME/magique, isolation des tenants, en-têtes HTTP de sécurité, CSRF, CORS).
5. **L'infrastructure de production** (`docker-compose.prod.yml`, Nginx HTTPS/reverse proxy, scripts de backup/restauration PostgreSQL, configuration Prometheus & APM).
6. **Les endpoints de monitoring et santé système** (`GET /system/health`, `GET /billing/...`).

---

## 2. Architecture de Facturation & Abonnements

### 2.1. Grille des Plans & Quotas

| Métrique | Plan FREE | Plan PRO | Plan BUSINESS | Plan ENTERPRISE |
| :--- | :--- | :--- | :--- | :--- |
| **Documents importés** | 5 | 50 | 250 | Illimité (`-1`) |
| **Pages analysées** | 50 | 1 000 | 10 000 | Illimité (`-1`) |
| **Stockage (Go / Mo)** | 100 Mo | 2 Go | 20 Go | Sur-mesure (`-1`) |
| **Générations IA** | 10 | 250 | 2 500 | Illimité (`-1`) |
| **Jetons LLM (Tokens)** | 50 000 | 1 000 000 | 10 000 000 | Sur-mesure (`-1`) |
| **Minutes Audio (TTS)** | 15 min | 180 min (3h) | 1 200 min (20h) | Illimité (`-1`) |
| **Présentations (Slides)** | 20 | 200 | 1 000 | Illimité (`-1`) |
| **QCM & Examens** | 10 | 100 | 1 000 | Illimité (`-1`) |
| **Support & SLA** | Communauté | Email prioritaire | Dédié 24/7 | SLA 99.9% + Account Mgr |

### 2.2. Modèles de Données

#### `Subscription` (`billing_subscription`)
- `id` : UUID unique (PK).
- `organization` : Relation OneToOne avec `Organization`.
- `plan` : Choix (`FREE`, `PRO`, `BUSINESS`, `ENTERPRISE`).
- `status` : Statut du contrat (`ACTIVE`, `TRIALING`, `PAST_DUE`, `CANCELED`).
- `started_at`, `current_period_end`, `canceled_at`.
- `billing_provider` : Fournisseur actif (`mock`, `stripe`, etc.).
- `provider_customer_id`, `provider_subscription_id` : Identifiants externes.

#### `UsageRecord` (`billing_usagerecord`)
- `id` : UUID unique (PK).
- `organization` : Clé étrangère vers l'organisation.
- `metric` : Identifiant de métrique (`documents`, `pages`, `storage`, `ai_generations`, `tokens`, `audio`, `slides`, `quizzes`).
- `quantity` : Compteur entier incrémenté de façon atomique (`F()` expression).
- `period_start`, `period_end` : Cycle de facturation.
- Contrainte d'unicité : `("organization", "metric")`.

#### `AuditLog` (`billing_auditlog`)
- `id` : UUID unique.
- `organization` : Organisation concernée (nullable pour actions système globales).
- `actor` : Utilisateur initiateur de l'action (`AUTH_USER_MODEL`).
- `action` : Nom qualifié de l'action (`course.created`, `subscription.plan_changed`, etc.).
- `resource_type`, `resource_id` : Cible de l'opération.
- `ip_address` : Adresse IP cliente (résolue via `X-Forwarded-For` ou `REMOTE_ADDR`).
- `user_agent` : Chaîne de l'agent utilisateur client.
- `metadata` : Dictionnaire JSON de contexte et paramètres.
- `created_at` : Horodatage immuable (indexé pour consultation rapide).

### 2.3. Abstraction BillingProvider

Pour éviter tout couplage fort avec un prestataire de paiement spécifique, le module expose `BaseBillingProvider` :
```python
class BaseBillingProvider(ABC):
    def create_customer(self, organization) -> str: ...
    def create_subscription(self, organization, plan: str) -> dict: ...
    def cancel_subscription(self, subscription) -> bool: ...
    def change_plan(self, subscription, new_plan: str) -> dict: ...
    def get_subscription_status(self, subscription) -> dict: ...
    def handle_webhook(self, payload: dict, signature: str = "") -> dict: ...
```
L'implémentation par défaut `MockBillingProvider` garantit l'exécution fluide des tests unitaires et du développement local sans cartes bancaires ni clés API tierces.

---

## 3. Moteur de Quotas (`QuotaService`)

Le service `QuotaService` fournit les garanties suivantes :
1. **Vérification avant action** : `check_quota(org, metric, amount) -> (is_allowed, current, limit)`.
2. **Incrémentation atomique** : `increment_usage(org, metric, amount)` utilise `select_for_update()` et `F('quantity') + amount` pour éviter les conditions de concurrence lors de requêtes simultanées.
3. **Rejet strict avec exception explicite** : `check_and_increment()` déclenche une `QuotaExceededException` (HTTP 403 Forbidden) lorsque le plafond du plan est atteint.
4. **Plans illimités** : Support natif du plafond `-1` pour les organisations Enterprise.
5. **Rapport d'utilisation consolidé** : `get_usage_summary(org)` calcule en temps réel le pourcentage, le restant et le statut pour chaque métrique.

---

## 4. Revue Complète de Sécurité & Durcissement

| Domaine de Sécurité | Mesures & Implémentation |
| :--- | :--- |
| **Isolation Multi-Tenant** | Toutes les requêtes filtrent strictement sur l'appartenance de l'utilisateur (`organization__members__user=request.user`). Un utilisateur ne peut ni consulter ni modifier les abonnements, usages ou données d'un autre tenant. |
| **Permissions Granulaires** | Les modifications d'abonnement et la consultation des journaux d'audit requièrent le rôle `OWNER` ou `ADMIN` au sein de l'organisation. |
| **Rate Limiting (DRF & Nginx)** | Double niveau de limitation : au niveau applicatif (`AnonRateThrottle` 120/min, `UserRateThrottle` 1200/min, `uploads` 30/min, `ai` 60/min) et au niveau Nginx (`limit_req_zone` 30r/s sur l'API, 5r/s sur l'authentification). |
| **Sécurité des Uploads & Validation MIME** | `validate_file_security()` bloque immédiatement les extensions exécutables dangereuses (`.exe`, `.sh`, `.py`, `.php`, `.js`, etc.), vérifie l'absence de traversée de chemin (`..`, octets nuls), valide la taille maximale et contrôle les signatures binaires magiques (magic bytes pour PDF `%PDF-`, DOCX/PPTX `PK\x03\x04`, MP3 `ID3`, etc.). |
| **En-têtes de Sécurité HTTP** | Nginx et Django injectent : `Strict-Transport-Security` (HSTS preload), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`. |
| **Protection Cookies & Sessions** | `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`, `CSRF_COOKIE_HTTPONLY = True`. |
| **Sécurité Nginx pour les Fichiers Médias** | Interdiction stricte de l'exécution de tout script dans `/media/` (`deny all` pour `.php`, `.py`, `.sh`, etc.). |
| **Audit Trail Immuable** | Enregistrement de chaque action critique (changement d'abonnement, téléversement de documents, etc.) avec horodatage, adresse IP réelle et agent utilisateur. |

---

## 5. Infrastructure de Production

### 5.1. Fichiers Déployés
- `docker-compose.prod.yml` : Orchestration de production (PostgreSQL avec pgvector, Redis persistant, API Django via Gunicorn multi-threads, Celery Worker, Celery Beat, Frontend Next.js, Nginx).
- `infrastructure/nginx/production.conf` : Configuration Nginx sécurisée pour HTTPS, HTTP/2, compression Gzip, SSL TLS 1.2/1.3 et proxying inverse.
- `infrastructure/postgres/backup.sh` : Script de sauvegarde automatisé avec compression gzip, hachage SHA-256 pour validation d'intégrité et rotation automatique (rétention 7 jours).
- `infrastructure/postgres/restore.sh` : Script de restauration sécurisé avec contrôle d'intégrité préalable.
- `infrastructure/monitoring/prometheus.yml` : Configuration de collecte de métriques Prometheus.
- `apps/api/config/settings/production.py` : Configuration Django de production avec intégration APM Sentry.

### 5.2. Commandes d'Exploitation Production

```bash
# 1. Démarrer la stack de production en arrière-plan
docker compose -f docker-compose.prod.yml up -d --build

# 2. Exécuter les migrations de base de données
docker compose -f docker-compose.prod.yml exec api python manage.py migrate

# 3. Collecter les fichiers statiques
docker compose -f docker-compose.prod.yml exec api python manage.py collectstatic --noinput

# 4. Déclencher une sauvegarde manuelle de la base de données
docker compose -f docker-compose.prod.yml exec postgres /bin/bash /scripts/backup.sh

# 5. Consulter la santé de l'infrastructure
curl -k https://localhost/system/health
```

---

## 6. Endpoints de l'API Sprint 14

| Méthode | Route | Description | Accès |
| :--- | :--- | :--- | :--- |
| `GET` | `/billing/plan` (ou `/api/v1/billing/plan`) | Liste des 4 plans SaaS avec quotas et liste de fonctionnalités | Public |
| `GET` | `/billing/usage` (ou `/api/v1/billing/usage`) | Détail de consommation actuelle, limites, % et restant | Authentifié (Membre) |
| `GET` | `/billing/subscription` | Informations de l'abonnement en cours et statut | Authentifié (Membre) |
| `POST` | `/billing/subscription` | Mise à niveau ou changement de plan (`FREE`, `PRO`, etc.) | Authentifié (`OWNER` ou `ADMIN`) |
| `GET` | `/billing/audit-logs` | Journal d'audit chronologique de l'organisation | Authentifié (`OWNER` ou `ADMIN`) |
| `GET` | `/system/health` (ou `/api/v1/health`) | Diagnostic de santé système (PostgreSQL, Cache Redis, Storage, Celery) | Public / Monitoring |

---

## 7. Validation des Tests

La suite complète de tests automatisés couvre tous les modules du projet de manière exhaustive :

```
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1
django: version: 5.1.15, settings: config.settings.test
collected 196 items

apps/api/tests/test_analytics.py .........                               [  4%]
apps/api/tests/test_audio.py ............                                [ 10%]
apps/api/tests/test_auth.py ............                                 [ 16%]
apps/api/tests/test_billing.py .....................                     [ 27%]
apps/api/tests/test_chat.py ...........                                  [ 32%]
apps/api/tests/test_courses.py ..........                                [ 37%]
apps/api/tests/test_documents.py ............                            [ 43%]
apps/api/tests/test_generation.py ...................                    [ 53%]
apps/api/tests/test_health.py ..                                         [ 54%]
apps/api/tests/test_ingestion.py ..................                      [ 63%]
apps/api/tests/test_learning.py ..........                               [ 68%]
apps/api/tests/test_organizations.py ...........                         [ 74%]
apps/api/tests/test_quizzes.py ..........                                [ 79%]
apps/api/tests/test_rag.py ............                                  [ 85%]
apps/api/tests/test_slides.py .................                          [ 94%]
apps/api/tests/test_celery.py ..                                         [ 95%]
apps/api/tests/test_settings.py ...                                      [100%]

============================ 196 passed in 24.27s =============================
```

**Résultat : 196 tests exécutés avec succès (100% de réussite).**
