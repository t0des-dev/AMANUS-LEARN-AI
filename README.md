# AMANUS LEARN AI

> Plateforme SaaS EdTech / IA / RAG / LMS de transformation automatisée de documents pédagogiques et professionnels en contenus d'apprentissage interactifs.

---

## Architecture Monorepo

```
amanus-learn-ai/
├── apps/
│   ├── web/                     # Frontend Next.js (App Router, Tailwind, TypeScript)
│   └── api/                     # Backend Django REST Framework, Celery, PostgreSQL
├── workers/                     # Workers Celery spécialisés (Documents, AI, Audio, Slides)
├── infrastructure/              # Dockerfiles, Nginx & scripts Postgres
├── docs/                        # Architecture, API & suivi des Sprints
└── docker-compose.yml           # Orchestration locale et production
```

---

## Démarrage Rapide

### 1. Démarrage complet avec Docker Compose
Le projet démarre entièrement avec une commande unique :

```bash
docker compose up -d
```

Services démarrés :
- **Frontend Web** : [http://localhost:3000](http://localhost:3000) (ou via Nginx sur [http://localhost](http://localhost))
- **Backend API REST** : [http://localhost:8000](http://localhost:8000)
- **Health Check** : [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Documentation OpenAPI / Swagger** : [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **PostgreSQL + pgvector** : Port `5432`
- **Redis** : Port `6379`
- **MinIO Console (S3)** : [http://localhost:9001](http://localhost:9001)
- **Celery Worker & Beat** : Tâches d'arrière-plan

---

### 2. Démarrage Local (Sans Docker)

#### Backend Django API :
```bash
# Activation de l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# Application des migrations
cd apps/api
python manage.py migrate

# Lancement du serveur API
python manage.py runserver
```

#### Frontend Next.js :
```bash
cd apps/web
npm run dev
```

---

## Tests & Assurance Qualité

```bash
# Tests backend Django (Pytest)
pytest apps/api

# Linting Python
ruff check apps/api

# Type checking Frontend
cd apps/web
npm run typecheck

# Build Frontend
npm run build
```

---

## Suivi des Sprints
- **Sprint 00 : Foundation / Architecture** — ✅ Terminé et Validé
- **Sprint 01 : Authentification & Multi-Tenancy** — ⏳ En attente de lancement
