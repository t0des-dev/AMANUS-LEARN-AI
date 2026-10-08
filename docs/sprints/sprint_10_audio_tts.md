# SPRINT 10 — AUDIO / TTS : Rapport de Réalisation & Validation

## 1. Objectif du Sprint
Transformer les cours et leçons didactiques en capsules audio interactives (**Audio / TTS**) pour la plateforme **Amanus Learn AI** :
- Modélisation relationnelle complète du contenu audio (`AudioContent`).
- Architecture modulaire et découplée de synthèse vocale avec `BaseTTSProvider` (supportant `MockTTSProvider`, `OpenAITTSProvider`, `ElevenLabsTTSProvider`).
- Pipeline de transformation automatisé en 4 étapes :
  $$\text{Lesson} \longrightarrow \text{Pedagogical Script} \longrightarrow \text{TTS Synthesis} \longrightarrow \text{Audio File} \longrightarrow \text{Storage Persistence}$$
- Traitement **100% asynchrone non-bloquant** via Celery (`generate_section_audio_task`).
- API REST sécurisée et isolée multi-tenant (`/sections/{id}/audio`, `/audio/{id}`, `/audio/voices`).
- Composants Next.js (`AudioPlayer`, `AudioProgress`, `VoiceSelector`, `AudioGenerationButton`) prenant en charge :
  - **pause**
  - **resume**
  - **progress**
  - **duration**

---

## 2. Modèle Relationnel (`apps/api/apps/audio/models.py`)

### `AudioContent`
- `id` : Identifiant UUID unique.
- `course` : Clé étrangère vers `Course`.
- `section` : Clé étrangère vers `CourseSection` (liaison à la leçon/chapitre).
- `language` : Langue de synthèse (`fr`, `en`, etc.).
- `voice_provider` : Fournisseur TTS sélectionné (`mock`, `openai`, `elevenlabs`).
- `voice_id` : Identifiant de la voix (ex: `pierre`, `marie`, `alloy`, `rachel`).
- `script` : Script pédagogique oralisé généré automatiquement ou fourni sur mesure.
- `storage_key` : Chemin d'accès au fichier audio persistant (Local / MinIO / S3).
- `duration` : Durée précise calculée en secondes.
- `status` : Cycle de vie (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- `error_message` : Traçabilité des éventuelles erreurs d'inférence ou de stockage.
- Méthode `get_audio_url()` : Fournit l'URL publique ou pré-signée de streaming direct.

---

## 3. Architecture Modulaire TTS (`apps/api/apps/audio/services/providers/`)

L'architecture est entièrement découplée de tout fournisseur spécifique grâce au patron de conception *Strategy* / *Adapter* :

- `BaseTTSProvider` : Interface abstraite avec `synthesize(text, voice_id, language)` et `get_available_voices(language)`.
- `MockTTSProvider` : Synthétiseur déterministe avec calcul de débit vocal (~130 mots/min) et génération de flux binaire MP3 valide avec en-tête ID3v2.
- `OpenAITTSProvider` : Intégration de l'API OpenAI Audio Speech (`model: tts-1`, voix `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`) avec repli automatique sur Mock si pas de clé API.
- `ElevenLabsTTSProvider` : Intégration de l'API ElevenLabs avec voix expressives et multilingues.
- `get_tts_provider(name)` & `list_available_voices()` : Fabrique et agrégateur de voix.

---

## 4. Pipeline Pédagogique Spoken Script & Asynchronisme Celery

### 4.1 Générateur de Script Pédagogique (`PedagogicalScriptGenerator`)
Spécifiquement conçu pour l'écoute humaine :
- Nettoie les balises markdown (`#`, `**`, `*`, `_`), les liens et les marqueurs de citations documentaires `[1]`.
- Convertit les blocs de code en transitions orales explicatives.
- Transforme les listes à puces brutes en enchaînements rhétoriques ("Retenons notamment...", "Puis...", "Enfin...").
- Ajoute une introduction chaleureuse ("Bonjour et bienvenue dans cette leçon intitulée...") et une synthèse de conclusion.

### 4.2 Exécution Asynchrone Celery (`generate_section_audio_task`)
- La requête `POST /sections/{id}/audio` crée l'entité `AudioContent` à l'état `PENDING` et délègue la tâche au worker Celery sans bloquer le serveur HTTP (réponse immédiate `HTTP 202 Accepted`).
- Le worker passe l'état à `PROCESSING`, exécute la transformation, sauvegarde le fichier MP3 dans le service de stockage via `save_file`, calcule la durée réelle, et marque l'audio comme `COMPLETED`.

---

## 5. API Endpoints

Tous les endpoints sont montés sous `/api/v1/` :
- `POST /api/v1/sections/{id}/audio` : Demande de génération audio pour une section (asynchrone Celery).
- `GET  /api/v1/sections/{id}/audio` : Consultation de l'audio existant d'une section.
- `GET  /api/v1/audio/{id}` : Récupération des détails (statut, durée, transcription, `audio_url`).
- `DELETE /api/v1/audio/{id}` : Suppression de l'entité en base et purge physique du fichier audio dans le stockage.
- `GET  /api/v1/audio/voices` : Liste des voix disponibles pour le `VoiceSelector`.

---

## 6. Composants Next.js (`apps/web/components/audio/`)

1. **`AudioPlayer`** :
   - Prise en charge native de **Play**, **Pause (Pause/Resume)**, saut $\pm$10s, réglage de vitesse (0.75x, 1x, 1.25x, 1.5x) et contrôle de volume/mute.
   - Volet dépliable affichant la transcription pédagogique synchronisée.
2. **`AudioProgress`** :
   - Barre de progression interactive avec scrubber cliquable/glissable (seek).
   - Horodatage `mm:ss` (temps écoulé et durée totale) et mise en mémoire tampon.
3. **`VoiceSelector`** :
   - Sélection visuelle des voix par langue (Français / Anglais), genre et caractéristiques.
4. **`AudioGenerationButton`** :
   - Bouton contextuel intégré dans l'en-tête de leçon de `LessonViewer`.
   - Gestion dynamique des états (`PENDING`/`PROCESSING` avec polling automatique toutes les 2.5s, `COMPLETED` avec bascule directe vers le lecteur).

---

## 7. Résultats des Tests & Validation

### Backend Django (`pytest apps/api/tests/test_audio.py`)
```bash
apps\api\tests\test_audio.py ............                                [100%]
============================= 12 passed in 0.84s ==============================
```
- Tests de synthèse du `MockTTSProvider` (MP3 binaire valide, calcul durée).
- Tests de repli sans clé API pour `OpenAITTSProvider`.
- Tests de nettoyage et d'oralisation du `PedagogicalScriptGenerator`.
- Test de déclenchement non-bloquant de la tâche Celery (`POST /sections/{id}/audio` $\rightarrow$ `HTTP 202 Accepted`).
- Test de bout en bout du pipeline (`AudioPipelineService`).
- Test de suppression en base et de purge du fichier dans le stockage.
- Test de cloisonnement multi-tenant (interdiction d'accès ou de génération inter-organisations).

**Suite globale de tests : 139 tests réussis sur 139** (`pytest apps/api/tests/`, 0 régression).

### Frontend Next.js
- `npm run typecheck` : **0 erreur TypeScript**.
- `npm run build` : **Compilation réussie** (15/15 routes statiques et dynamiques).
