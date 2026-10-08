# Spécification API — Version 1 (/api/v1/)

## Endpoints Actifs

### 1. Health Check
- **Méthode** : `GET`
- **Chemin** : `/api/v1/health`
- **Authentification** : Aucune (Publique)
- **Description** : Sonde de vitalité pour load balancers, conteneurs et frontend.

#### Réponse HTTP 200 OK
```json
{
  "status": "ok"
}
```

---

### 2. Authentification & Profil (`/api/v1/auth/`)

#### 2.1 Inscription
- **Méthode** : `POST`
- **Chemin** : `/api/v1/auth/register`
- **Authentification** : Aucune (Publique)
- **Corps de requête** :
  ```json
  {
    "email": "utilisateur@organisation.com",
    "password": "Password123!",
    "password_confirm": "Password123!",
    "first_name": "Jean",
    "last_name": "Dupont",
    "language": "fr"
  }
  ```
- **Réponse HTTP 201 Created** :
  ```json
  {
    "user": {
      "id": "uuid-v4",
      "email": "utilisateur@organisation.com",
      "first_name": "Jean",
      "last_name": "Dupont",
      "avatar": null,
      "language": "fr",
      "is_active": true,
      "created_at": "2026-10-05T12:00:00Z",
      "updated_at": "2026-10-05T12:00:00Z"
    },
    "access": "jwt-access-token",
    "refresh": "jwt-refresh-token"
  }
  ```

#### 2.2 Connexion
- **Méthode** : `POST`
- **Chemin** : `/api/v1/auth/login`
- **Authentification** : Aucune (Publique)
- **Corps de requête** :
  ```json
  {
    "email": "utilisateur@organisation.com",
    "password": "Password123!"
  }
  ```
- **Réponse HTTP 200 OK** : identique à la structure d'inscription.

#### 2.3 Rafraîchissement de Token
- **Méthode** : `POST`
- **Chemin** : `/api/v1/auth/refresh`
- **Authentification** : Aucune (Publique)
- **Corps de requête** :
  ```json
  {
    "refresh": "jwt-refresh-token"
  }
  ```
- **Réponse HTTP 200 OK** :
  ```json
  {
    "access": "new-jwt-access-token"
  }
  ```

#### 2.4 Déconnexion
- **Méthode** : `POST`
- **Chemin** : `/api/v1/auth/logout`
- **Authentification** : Optionnelle
- **Corps de requête** :
  ```json
  {
    "refresh": "jwt-refresh-token"
  }
  ```
- **Réponse HTTP 200 OK** :
  ```json
  {
    "detail": "Déconnexion réussie."
  }
  ```

#### 2.5 Profil Utilisateur Courant (Consultation)
- **Méthode** : `GET`
- **Chemin** : `/api/v1/auth/me`
- **Authentification** : **Bearer JWT** obligatoire
- **Réponse HTTP 200 OK** : objet `user`.

#### 2.6 Profil Utilisateur Courant (Mise à Jour)
- **Méthode** : `PATCH`
- **Chemin** : `/api/v1/auth/me`
- **Authentification** : **Bearer JWT** obligatoire
- **Corps de requête** :
  ```json
  {
    "first_name": "Jean-Marc",
    "last_name": "Dupont",
    "language": "en"
  }
  ```
- **Réponse HTTP 200 OK** : objet `user` mis à jour.

---

### 3. Gestion Documentaire & Ingestion (`/api/v1/documents/`)

#### 3.1 Déclencher le Traitement (Ingestion Celery)
- **Méthode** : `POST`
- **Chemin** : `/api/v1/documents/{id}/process/`
- **Authentification** : **Bearer JWT** (Membres autorisés du tenant)
- **Réponse HTTP 200 OK** :
  ```json
  {
    "id": "uuid-v4",
    "status": "EXTRACTING",
    "task_id": "celery-task-id",
    "message": "Pipeline de traitement initialisé avec succès."
  }
  ```

#### 3.2 Statut Détaillé de Progression
- **Méthode** : `GET`
- **Chemin** : `/api/v1/documents/{id}/processing-status/`
- **Authentification** : **Bearer JWT** (Membres du tenant)
- **Réponse HTTP 200 OK** :
  ```json
  {
    "id": "uuid-v4",
    "status": "COMPLETED",
    "progress_stage": "Completed",
    "page_count": 5,
    "pages_count": 5,
    "chunks_count": 12,
    "error_message": "",
    "updated_at": "2026-10-06T18:00:00Z"
  }
  ```

#### 3.3 Pages Extraites & Structure Hiérarchique
- **Méthode** : `GET`
- **Chemin** : `/api/v1/documents/{id}/pages/`
- **Authentification** : **Bearer JWT** (Membres du tenant)
- **Réponse HTTP 200 OK** :
  ```json
  {
    "count": 5,
    "document_id": "uuid-v4",
    "results": [
      {
        "id": "uuid-v4",
        "document": "uuid-v4",
        "page_number": 1,
        "text": "Texte extrait...",
        "ocr_used": false,
        "metadata": {
          "chapter": "Chapitre 1 : Introduction",
          "section": "Section 1.1 : Contexte",
          "subsection": "Sous-section 1.1.1 : Détails",
          "headings": ["..."]
        },
        "created_at": "2026-10-06T18:00:00Z",
        "updated_at": "2026-10-06T18:00:00Z"
      }
    ]
  }
  ```

---

### 4. Moteur RAG & Recherche Vectorielle (`/api/v1/rag/`)

#### 4.1 Recherche Vectorielle Filtrée par Tenant
- **Méthode** : `POST`
- **Chemin** : `/api/v1/rag/search/`
- **Authentification** : **Bearer JWT** (Membres du tenant)
- **Corps de requête** :
  ```json
  {
    "query": "Comment fonctionne l'attention multi-têtes ?",
    "organization_id": "uuid-v4",
    "document_id": "uuid-v4 (optionnel)",
    "top_k": 5
  }
  ```
- **Réponse HTTP 200 OK** :
  ```json
  {
    "query": "Comment fonctionne l'attention multi-têtes ?",
    "organization_id": "uuid-v4",
    "document_id": null,
    "count": 1,
    "results": [
      {
        "chunk_id": "uuid-v4",
        "document_id": "uuid-v4",
        "document_title": "Manuel de Deep Learning",
        "page": 1,
        "page_number": 1,
        "chapter": "Chapitre 1 : Les Transformers",
        "section": "1.1 Attention",
        "subsection": null,
        "chunk_index": 0,
        "content": "L'attention multi-têtes permet au modèle...",
        "score": 0.8854,
        "distance": 0.1146
      }
    ]
  }
  ```

#### 4.2 Requête RAG avec Contexte et Citations
- **Méthode** : `POST`
- **Chemin** : `/api/v1/rag/query/`
- **Authentification** : **Bearer JWT** (Membres du tenant)
- **Corps de requête** : identique à `/search/`
- **Réponse HTTP 200 OK** :
  ```json
  {
    "query": "Comment fonctionne l'attention multi-têtes ?",
    "organization_id": "uuid-v4",
    "document_id": null,
    "count": 1,
    "results": [ ... ],
    "citations": [
      {
        "citation_id": 1,
        "chunk_id": "uuid-v4",
        "document_id": "uuid-v4",
        "document_title": "Manuel de Deep Learning",
        "page": 1,
        "chapter": "Chapitre 1 : Les Transformers",
        "section": "1.1 Attention",
        "snippet": "L'attention multi-têtes permet au modèle...",
        "score": 0.8854
      }
    ],
    "context": "--- Source [1] : Manuel de Deep Learning (ID: ...) | Page: 1 | Chapitre: Chapitre 1 ... ---\n...",
    "prompt": "Contexte documentaire extrait : ... Question : ... Consignes strictes : ...",
    "sources_summary": "### Sources documentaires :\n- **[1]** **Manuel de Deep Learning** | Page 1 | ..."
  }
  ```

### 5. Moteur de Génération Pédagogique IA (`/api/v1/documents/{id}/generate/`)

Toutes les générations IA sont traçables, sauvegardées dans la table d'audit `ai_generation`, et strictement fondées sur le RAG documentaire.

#### 5.1 Générer un Résumé Structuré
- **Méthode** : `POST`
- **Chemin** : `/api/v1/documents/{id}/generate/summary/`
- **Authentification** : **Bearer JWT** (Membres de l'organisation)
- **Corps de requête** (optionnel) :
  ```json
  {
    "provider": "openai",
    "model": "gpt-4o",
    "focus": "Mettre l'accent sur les mécanismes d'attention",
    "top_k": 5
  }
  ```
- **Réponse HTTP 201 Created** :
  ```json
  {
    "id": "uuid-v4",
    "organization": "uuid-v4",
    "user": "uuid-v4",
    "document": "uuid-v4",
    "type": "SUMMARY",
    "provider": "openai",
    "model": "gpt-4o",
    "prompt_version": "summary-v1.0",
    "input_tokens": 1250,
    "output_tokens": 420,
    "status": "SUCCESS",
    "result": {
      "overview": "Synthèse globale du document...",
      "key_takeaways": ["Point 1 [1]", "Point 2 [2]"],
      "chapters_summary": [
        {
          "title": "Introduction aux Transformers",
          "summary": "Exposé des fondements..."
        }
      ],
      "citations": [ ... ],
      "sources_summary": "### Sources documentaires : ..."
    },
    "error": "",
    "created_at": "2026-10-06T20:00:00Z"
  }
  ```

#### 5.2 Générer un Cours Pédagogique
- **Méthode** : `POST`
- **Chemin** : `/api/v1/documents/{id}/generate/course/`
- **Authentification** : **Bearer JWT** (Membres de l'organisation)
- **Réponse HTTP 201 Created** : objet `AIGeneration` avec type `LESSON`.

#### 5.3 Extraire les Objectifs d'Apprentissage
- **Méthode** : `POST`
- **Chemin** : `/api/v1/documents/{id}/generate/objectives/`
- **Authentification** : **Bearer JWT** (Membres de l'organisation)
- **Réponse HTTP 201 Created** : objet `AIGeneration` avec type `OBJECTIVES`.

#### 5.4 Extraire les Notions & Points Clés
- **Méthode** : `POST`
- **Chemin** : `/api/v1/documents/{id}/generate/key-points/`
- **Authentification** : **Bearer JWT** (Membres de l'organisation)
- **Réponse HTTP 201 Created** : objet `AIGeneration` avec type `KEY_POINTS`.

---

### 6. Course Builder & Gestion des Cours (`/api/v1/courses/` et `/api/v1/sections/`)

Gestion complète des cours et de leur hiérarchie (Course -> Chapter -> Section -> Lesson).
Le contenu généré par l'IA est entièrement éditable par les enseignants (`PATCH /sections/{id}/`).

#### 6.1 Lister les Cours
- **Méthode** : `GET`
- **Chemin** : `/api/v1/courses/`
- **Filtres optionnels** : `?organization_id={uuid}&status=DRAFT|PUBLISHED&level=BEGINNER`
- **Authentification** : **Bearer JWT** (Membres de l'organisation)

#### 6.2 Créer un Cours
- **Méthode** : `POST`
- **Chemin** : `/api/v1/courses/`
- **Authentification** : **Bearer JWT** (Enseignants, Admins, Propriétaires)
- **Corps de requête** :
  ```json
  {
    "organization": "uuid-v4",
    "title": "Introduction au Deep Learning",
    "description": "Cours complet structuré",
    "language": "fr",
    "level": "BEGINNER",
    "document": "uuid-v4"
  }
  ```

#### 6.3 Détail d'un Cours (avec Sommaire Hiérarchique Arborescent)
- **Méthode** : `GET`
- **Chemin** : `/api/v1/courses/{id}/`
- **Authentification** : **Bearer JWT** (Membres de l'organisation)

#### 6.4 Mettre à Jour un Cours
- **Méthode** : `PATCH`
- **Chemin** : `/api/v1/courses/{id}/`
- **Authentification** : **Bearer JWT** (Enseignants, Admins, Propriétaires)

#### 6.5 Supprimer un Cours
- **Méthode** : `DELETE`
- **Chemin** : `/api/v1/courses/{id}/`
- **Authentification** : **Bearer JWT** (Enseignants, Admins, Propriétaires)

#### 6.6 Gestion des Sections / Chapitres d'un Cours
- `GET  /api/v1/courses/{id}/sections/` : Lister les chapitres racines avec leurs sous-sections et leçons
- `POST /api/v1/courses/{id}/sections/` : Créer une section (avec `parent: null` pour Chapitre, ou `parent: uuid` pour sous-section/leçon)

#### 6.7 Édition Pédagogique d'une Leçon / Section
- `GET    /api/v1/sections/{id}/` : Obtenir les détails et le contenu d'une leçon
- `PATCH  /api/v1/sections/{id}/` : **Modifier le contenu didactique**, le résumé, les objectifs et la durée (Édition du contenu IA)
- `DELETE /api/v1/sections/{id}/` : Supprimer une leçon ou section

#### 6.8 Génération IA Pédagogique d'un Cours à Partir d'un Document
- **Méthode** : `POST`
- **Chemin** : `/api/v1/courses/{id}/generate/`
- **Authentification** : **Bearer JWT** (Enseignants, Admins, Propriétaires)
- **Corps de requête** (optionnel) :
  ```json
  {
    "document_id": "uuid-v4",
    "provider": "openai",
    "model": "gpt-4o",
    "top_k": 10
  }
  ```
- **Effet** : Génère et matérialise l'arborescence complète (Chapitres -> Sections -> Leçons) à partir du document analysé via le RAG. Tout le contenu généré est modifiable.

---

### 7. Moteur de QCM & Évaluations (`/api/v1/courses/{id}/quizzes/` et `/api/v1/quizzes/`)

Le moteur de QCM supporte trois modes pédagogiques (`TRAINING`, `EXAM`, `REVISION`), des niveaux de difficulté (`EASY`, `MEDIUM`, `HARD`), la génération assistée par IA avec validation stricte avant insertion, et le calcul automatisé des scores, tentatives et temps passé.

#### 7.1 Lister et Créer les Quiz d'un Cours
- `GET  /api/v1/courses/{id}/quizzes/` : Liste tous les quiz associés à un cours
- `POST /api/v1/courses/{id}/quizzes/` : Crée un nouveau quiz associé à ce cours (Rôle : Enseignant, Admin, Propriétaire)

#### 7.2 Lister et Créer des Quiz Généraux
- `GET  /api/v1/quizzes/` : Liste les quiz avec filtres `?organization_id={uuid}&quiz_type=TRAINING|EXAM|REVISION&difficulty=EASY|MEDIUM|HARD`
- `POST /api/v1/quizzes/` : Crée un quiz (Enseignant, Admin, Propriétaire)
  ```json
  {
    "organization": "uuid-v4",
    "course": "uuid-v4 (optionnel)",
    "title": "Examen de Mi-Semestre",
    "description": "Évaluation portant sur les 3 premiers chapitres",
    "quiz_type": "EXAM",
    "difficulty": "MEDIUM",
    "time_limit_minutes": 20,
    "passing_score": 70
  }
  ```

#### 7.3 Détails d'un Quiz
- `GET /api/v1/quizzes/{id}/` : Récupère les métadonnées et la liste des questions avec leurs 4 choix de réponse.
  > **Note de sécurité et triche** : Pour les étudiants en cours d'évaluation, le champ `is_correct` est systématiquement masqué. Seuls les enseignants ou les résultats validés révèlent la bonne réponse.

#### 7.4 Génération IA de Questions avec Validation Stricte
- **Méthode** : `POST`
- **Chemin** : `/api/v1/quizzes/{id}/generate/`
- **Authentification** : **Bearer JWT** (Enseignant, Admin, Propriétaire)
- **Corps de requête** (optionnel) :
  ```json
  {
    "document_id": "uuid-v4 (optionnel)",
    "count": 5,
    "difficulty": "MEDIUM",
    "prompt": "Focaliser sur les principes d'optimisation"
  }
  ```
- **Sécurité IA** : Chaque question renvoyée par le LLM passe par le `QuizQuestionValidator` :
  1. Exactly 4 propositions de réponse.
  2. Exactly 1 bonne réponse (`is_correct = true`).
  3. Aucune réponse dupliquée.
  4. Explication pédagogique et source documentaire obligatoires.
  Toute question malformée est rejetée avant insertion en base.

#### 7.5 Démarrer une Tentative de Quiz
- **Méthode** : `POST`
- **Chemin** : `/api/v1/quizzes/{id}/start/`
- **Authentification** : **Bearer JWT** (Tout membre de l'organisation)
- **Réponse HTTP 201 Created** : Initialise une instance de `QuizAttempt` avec horodatage `started_at`.

#### 7.6 Soumettre une Tentative et Calculer le Score
- **Méthode** : `POST`
- **Chemin** : `/api/v1/quizzes/{id}/submit/`
- **Authentification** : **Bearer JWT** (Auteur de la tentative)
- **Corps de requête** :
  ```json
  {
    "attempt_id": "uuid-v4",
    "answers": [
      {
        "question_id": "uuid-v4",
        "selected_answer_id": "uuid-v4"
      }
    ]
  }
  ```
- **Réponse HTTP 200 OK** : Retourne la tentative clôturée avec le score (%), le statut `is_passed`, le temps passé en secondes et la correction détaillée (`results_breakdown`).

#### 7.7 Consulter l'Historique des Résultats
- **Méthode** : `GET`
- **Chemin** : `/api/v1/quizzes/{id}/results/`
- **Authentification** : **Bearer JWT** (Membres de l'organisation)
- **Réponse HTTP 200 OK** : Liste de toutes les tentatives de l'utilisateur avec score, réussite, durée et corrections pédagogiques.

---

### 8. Documentation Interactive OpenAPI / Swagger
- **Schéma brut** : `GET /api/schema/`
- **Interface Swagger** : `GET /api/docs/`
- **Interface ReDoc** : `GET /api/redoc/`



