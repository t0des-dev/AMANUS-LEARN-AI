# SPRINT 09 — AI TUTOR / CHAT : Rapport de Réalisation & Validation

## 1. Objectif du Sprint
Mettre en œuvre l'assistant pédagogique conversationnel (**AI Tutor**) pour la plateforme **Amanus Learn AI** :
- Modélisation relationnelle complète du chat (`ChatSession` et `ChatMessage`).
- Pipeline RAG conversationnel temps réel : Question $\rightarrow$ Historique $\rightarrow$ Retrieval $\rightarrow$ Context $\rightarrow$ LLM $\rightarrow$ Streaming $\rightarrow$ Sources.
- Prise en charge des **8 commandes pédagogiques officielles** :
  - **Explique-moi** (ou *Explique*)
  - **Simplifie**
  - **Résume**
  - **Donne un exemple** (ou *Exemple*)
  - **Interroge-moi**
  - **Fais-moi réviser** (ou *Révision*)
  - **Compare**
  - **Définis**
- Support du streaming en direct via **Server-Sent Events (SSE)**.
- Isolation stricte des données et limitation des réponses aux documents accessibles à l'utilisateur dans son organisation.
- Interface utilisateur Next.js complète avec composants modulaires (`ChatWindow`, `ChatMessage`, `ChatInput`, `SourceCitation`, `TypingIndicator`, `SuggestedPrompt`) et routes `/chat` et `/chat/[session_id]`.

---

## 2. Modèles Relationnels (`apps/api/apps/chat/models.py`)

### 2.1 `ChatSession`
Représente une session conversationnelle d'apprentissage :
- `id` : UUID unique.
- `organization` : Clé étrangère vers `Organization` (isolation multi-tenant stricte).
- `user` : Clé étrangère vers l'utilisateur propriétaire de la conversation.
- `title` : Intitulé de la session (généré automatiquement à partir de la première question ou personnalisable).
- `document` : Clé étrangère optionnelle vers `Document` permettant d'ancrer le dialogue sur un document spécifique.
- `course` : Clé étrangère optionnelle vers `Course`.
- `created_at`, `updated_at` : Horodatages.

### 2.2 `ChatMessage`
Enregistre chaque interaction au sein d'une session :
- `id` : UUID unique.
- `session` : Clé étrangère vers `ChatSession` (cascade).
- `role` : Rôle émetteur (`user`, `assistant`, `system`).
- `content` : Corps textuel du message.
- `command` : Code de la posture pédagogique détectée (`EXPLAIN`, `SIMPLIFY`, `SUMMARY`, `EXAMPLE`, `QUIZ`, `REVISION`, `COMPARE`, `DEFINE`).
- `sources` : JSON structuré contenant les citations précises issues du RAG (ID de citation, titre du document, page, chapitre, section, extrait textuel, score de similarité vectorielle).
- `tokens_used` : Consommation de tokens (prompt + réponse).
- `metadata` : Métadonnées d'inférence (modèle, fournisseur, requête nettoyée).
- `created_at` : Horodatage du message.

---

## 3. Pipeline Pédagogique & RAG Conversationnel

Chaque question adressée à l'assistant suit le cycle en 6 étapes :
```text
Question de l'étudiant
         ↓
1. Détermination du contexte (détection de commande + historique récent)
         ↓
2. Retrieval vectoriel (Retriever, VectorSearch & Reranker sur documents autorisés)
         ↓
3. Construction du contexte (ContextBuilder + CitationBuilder + Règle anti-hallucination)
         ↓
4. Interrogation LLM (AIProvider avec consigne pédagogique ciblée)
         ↓
5. Streaming temps réel (Server-Sent Events token par token)
         ↓
6. Restitution des sources (Citations structurées [1], [2] avec provenance complète)
```

### 3.1 Détection et Postures Pédagogiques (`apps/api/apps/chat/services/pedagogical_commands.py`)
Le système identifie automatiquement les commandes par :
1. Paramètre explicite (`command="EXPLAIN"`)
2. Commandes slash (`/explique`, `/simplifie`, `/resume`, `/exemple`, `/interroge`, `/revision`, `/compare`, `/definis`)
3. Formulation en langage naturel ("Explique-moi...", "Peux-tu vulgariser...", "Fais un résumé de...", "Donne un exemple pratique...", etc.)

À chaque commande correspond une consigne pédagogique précise :
- **EXPLAIN** : Explication détaillée, progressive et structurée pas à pas.
- **SIMPLIFY** : Vulgarisation pour débutant, sans jargon, basée sur des analogies concrètes du quotidien.
- **SUMMARY** : Synthèse percutante sous forme de points clés et idées maîtresses.
- **EXAMPLE** : Scénarios réels et cas concrets tirés ou inspirés des sources.
- **QUIZ** : Questions stimulantes sans donner immédiatement la réponse pour faire réfléchir l'étudiant.
- **REVISION** : Mini fiche de révision, points d'attention et pièges fréquents.
- **COMPARE** : Structure comparative claire (points communs, divergences, cas d'usage).
- **DEFINE** : Définition formelle, concise et exacte du terme dans son contexte.

---

## 4. API Endpoints (`apps/api/apps/chat/views.py`)

Tous les endpoints sont montés sous le préfixe `/api/v1/chat/` :
- `POST /api/v1/chat/sessions` : Création d'une session (optionnellement ancrée à un document).
- `GET /api/v1/chat/sessions` : Liste des sessions de l'utilisateur dans l'organisation active.
- `GET /api/v1/chat/sessions/{id}` : Récupération du détail de la session et de son fil de messages.
- `PATCH /api/v1/chat/sessions/{id}` : Mise à jour du titre ou de l'ancrage.
- `DELETE /api/v1/chat/sessions/{id}` : Suppression d'une session.
- `POST /api/v1/chat/sessions/{id}/messages` : Envoi d'une question.
  - Mode synchrone : Retourne `HTTP 201 Created` avec les messages utilisateur et assistant ainsi que les sources.
  - Mode streaming (`stream=true`) : Retourne `HTTP 200 OK` avec `Content-Type: text/event-stream; charset=utf-8` émettant les événements SSE :
    - `data: {"type": "start", "user_message_id": "...", "command": "..."}`
    - `data: {"type": "token", "content": "..."}`
    - `data: {"type": "done", "message_id": "...", "command": "...", "sources": [...], "content": "..."}`
- `GET /api/v1/chat/commands` : Liste des 8 commandes pédagogiques disponibles.

---

## 5. Composants Next.js (`apps/web/components/chat/`)

1. **`ChatWindow`** : Conteneur principal gérant l'état des messages, le flux SSE token par token, le scroll automatique et le repli fluide.
2. **`ChatMessage`** : Bulle de message affichant le rôle, le badge de la commande pédagogique, les puces de citations cliquables `[1]`, `[2]` dans le texte, et l'action de copie.
3. **`ChatInput`** : Zone de saisie extensible avec menu d'insertion rapide des commandes pédagogiques, indication du document d'ancrage et raccourci Entrée.
4. **`SourceCitation`** : Tiroir de sources interactif affichant le titre du document, le numéro de page, le chapitre, le score de pertinence (%) et l'extrait textuel authentifié.
5. **`TypingIndicator`** : Indicateur animé de réflexion avec effet lumineux et pulsation.
6. **`SuggestedPrompt`** : Grille et pilules de suggestions pédagogiques pour amorcer rapidement la révision.

Pages réalisées :
- **`/chat`** : Hub de conversation avec sélection de document, recherche et historique des échanges.
- **`/chat/[session_id]`** : Interface de dialogue plein écran avec streaming en temps réel.

---

## 6. Sécurité & Contrôle des Accès
- **Isolation Multi-Tenant** : Un utilisateur d'une organisation A ne peut en aucun cas accéder aux sessions ou aux documents d'une organisation B (retourne `HTTP 404 Not Found`).
- **Filtrage documentaire strict** : Le moteur RAG limite les recherches vectorielles exclusivement aux documents de l'organisation dans l'état `READY` / `COMPLETED`.
- **Règle Anti-Hallucination** : Si les documents ne contiennent pas l'information, l'assistant répond explicitement : *« Cette information n'est pas présente dans les documents disponibles. »*

---

## 7. Résultats des Tests & Validation

### Tests unitaires & intégration chat (`apps/api/tests/test_chat.py`)
- `test_all_eight_pedagogical_commands_detection` : **PASS** (Détection des 8 commandes et nettoyage des déclencheurs).
- `test_explicit_command_parameter_override` : **PASS** (Priorité de la commande explicite).
- `test_instructions_exist_for_all_commands` : **PASS** (Cohérence pédagogique).
- `test_pedagogical_commands_list_endpoint` : **PASS** (`GET /api/v1/chat/commands`).
- `test_create_and_list_chat_sessions` : **PASS** (Cycle de vie des sessions).
- `test_multi_tenant_and_user_isolation_on_sessions` : **PASS** (Cloisonnement inter-organisations).
- `test_cannot_bind_document_from_another_organization` : **PASS** (Rejet des documents non autorisés).
- `test_chat_message_sync_rag_and_citations` : **PASS** (Génération synchrone, scoring et provenance).
- `test_streaming_sse_endpoint` : **PASS** (Streaming SSE, événements `start`, `token`, `done`, persistance en base).
- `test_document_scoping_and_cross_tenant_isolation_in_chat` : **PASS** (Aucune fuite de données d'un autre tenant).
- `test_pedagogical_commands_variations_and_provenance` : **PASS** (Variations des commandes et citations associées).

**Résultat suite complète :**
```bash
apps/api/tests/test_chat.py ........... [100%]
11 passed in 1.55s

Suite complète : 127 passed in 4.59s (0 régression)
Build Next.js : ✓ Compiled successfully / static generation (15/15)
TypeScript typecheck : ✓ 0 error
```
