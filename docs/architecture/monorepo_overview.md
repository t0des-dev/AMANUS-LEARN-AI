# Architecture Monorepo & Déploiement

## 1. Structure Globale

```
amanus-learn-ai/
├── apps/
│   ├── web/                     # Frontend Next.js (App Router, Tailwind, React Query)
│   │   ├── app/                 # Pages (/, /login, /register, /dashboard)
│   │   ├── components/          # Composants réutilisables & layout
│   │   ├── features/            # Modules par domaine
│   │   ├── hooks/               # Custom hooks React
│   │   ├── lib/                 # Utilitaires & configuration client
│   │   ├── services/            # Couche API client
│   │   ├── types/               # Définitions TypeScript
│   │   └── tests/               # Tests unitaires & intégration front
│   │
│   └── api/                     # Backend Django REST Framework
│       ├── config/              # Configuration globale (settings, URLs, celery, WSGI/ASGI)
│       ├── apps/                # 13 sous-applications modulaires Django
│       │   ├── accounts/        # Utilisateurs, authentification & sécurité
│       │   ├── organizations/   # Multi-tenancy, organisations & workspaces
│       │   ├── documents/       # Métadonnées & gestion des fichiers
│       │   ├── ingestion/       # Pipeline d'extraction, parsing & chunking
│       │   ├── courses/         # Génération de cours et modules
│       │   ├── quizzes/         # QCM, évaluations & questions-réponses
│       │   ├── learning/        # Parcours pédagogiques & flashcards
│       │   ├── ai/              # Abstractions AIProvider, EmbeddingProvider
│       │   ├── chat/            # Assistant conversationnel & RAG
│       │   ├── audio/           # Abstractions TTSProvider & génération audio
│       │   ├── slides/          # Génération de diaporamas
│       │   ├── analytics/       # Mesures de progression & KPIs
│       │   └── notifications/  # Notifications in-app, webhooks & emails
│       └── manage.py
│
├── workers/                     # Tâches d'arrière-plan Celery distribuées
│   ├── document_worker/         # Extraction OCR & chunking
│   ├── ai_worker/               # Embeddings & inférence LLM
│   ├── audio_worker/            # Synthèse vocale & rendu audio
│   └── slide_worker/            # Construction des présentations
│
├── infrastructure/              # Conteneurs et orchestrations
│   ├── docker/                  # Dockerfiles (api, web, worker) & scripts d'entrée
│   ├── nginx/                   # Reverse-proxy Nginx avec routage /api et front
│   ├── postgres/                # Script SQL d'initialisation pgvector
│   └── monitoring/              # Configurations métriques & santé
│
├── docs/                        # Documentation vivante du projet
│   ├── architecture/            # Schémas & flux de données
│   ├── api/                     # Spécifications OpenAPI & routes REST
│   ├── product/                 # Vision produit & principes directeurs
│   └── sprints/                 # Suivi rigoureux Sprint 00 → 14
│
├── tests/                       # Tests e2e & d'intégration monorepo
├── docker-compose.yml           # Déploiement local & CI
├── .env.example                 # Modèle des variables d'environnement
├── README.md                    # Guide de démarrage rapide
└── LICENSE                      # Licence MIT
```

## 2. Flux Réseau & Services

```
[Utilisateur Navigateur]
        │
        ▼ (Port 80)
   [NGINX Reverse Proxy]
   ┌────┴──────────────────────────┐
   │ /                             │ /api/v1/
   ▼                               ▼
[web: Next.js (3000)]       [api: Django DRF (8000)]
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
     [PostgreSQL + pgvector]   [Redis]         [MinIO / S3]
                ▲                  ▲                  ▲
                │                  │                  │
                └───────────[Celery Workers]──────────┘
```
