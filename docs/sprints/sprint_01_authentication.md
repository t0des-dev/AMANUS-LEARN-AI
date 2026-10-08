# Rapport de Validation — SPRINT 01 : AUTHENTICATION

## 1. Objectif du Sprint
Mettre en œuvre le système d'authentification complet et sécurisé pour **Amanus Learn AI** sans développer les fonctionnalités métier (Organization, Documents, IA, RAG) :
- Custom User Django basé sur l'email (`accounts.User`).
- Endpoints d'authentification JWT complets sous `/api/v1/auth/*`.
- Composants Next.js (`LoginForm`, `RegisterForm`, `UserMenu`, `AuthProvider`, `ProtectedRoute`).
- Pages frontend (`/login`, `/register`, `/profile`, `/dashboard` protégé).
- Sécurisation de tous les endpoints privés (`/me`).
- Tests complets backend et frontend.

---

## 2. Fichiers Créés et Modifiés

### Fichiers Créés
1. `apps/api/apps/accounts/models.py` : Custom User model avec UUID, email unique normalisé, prénom, nom, avatar, langue, dates, et `UserManager`.
2. `apps/api/apps/accounts/migrations/0001_initial.py` : Migration initiale du modèle User.
3. `apps/api/apps/accounts/serializers.py` : `UserSerializer`, `UserUpdateSerializer`, `RegisterSerializer`, `LoginSerializer`, `LogoutSerializer`.
4. `apps/api/apps/accounts/views.py` : `RegisterView`, `LoginView`, `LogoutView`, `CurrentUserView`.
5. `apps/api/apps/accounts/urls.py` : Définition des routes `register`, `login`, `refresh`, `logout`, `me`.
6. `apps/api/tests/test_auth.py` : Suite complète de 12 tests d'authentification.
7. `apps/api/pyproject.toml` : Configuration Ruff adaptée aux conventions Django REST.
8. `apps/web/types/auth.ts` : Typages TypeScript pour utilisateurs, tokens, payloads et contexte d'authentification.
9. `apps/web/lib/authTokens.ts` : Gestionnaire de persistance sécurisée des tokens JWT et cache utilisateur en localStorage.
10. `apps/web/services/authService.ts` : Service API typé pour register, login, refresh, logout, getMe, updateMe.
11. `apps/web/components/auth/AuthProvider.tsx` : Contexte React global pour la gestion de session, restauration auto et rafraîchissement silencieux.
12. `apps/web/components/auth/ProtectedRoute.tsx` : Garde de route client avec redirection vers `/login`.
13. `apps/web/components/layout/UserMenu.tsx` : Menu déroulant utilisateur (initiales, profil, dashboard, déconnexion).
14. `apps/web/features/auth/LoginForm.tsx` : Formulaire de connexion avec gestion d'état, validation et feedback.
15. `apps/web/features/auth/RegisterForm.tsx` : Formulaire d'inscription avec confirmation de mot de passe et sélection de la langue.
16. `apps/web/app/profile/page.tsx` : Page protégée de consultation et de mise à jour du profil utilisateur.
17. `docs/sprints/sprint_01_authentication.md` : Présent rapport de validation.

### Fichiers Modifiés
1. `apps/api/requirements.txt` : Ajout de `djangorestframework-simplejwt` et `pillow`.
2. `apps/api/config/settings/base.py` : Déclaration de `AUTH_USER_MODEL = "accounts.User"`, `rest_framework_simplejwt`, `DEFAULT_AUTHENTICATION_CLASSES` et configuration `SIMPLE_JWT`.
3. `apps/api/config/urls.py` : Inclusion de `apps.accounts.urls` sous `/api/v1/auth/`.
4. `apps/web/components/Providers.tsx` : Intégration de `AuthProvider`.
5. `apps/web/components/layout/Navbar.tsx` : Intégration dynamique de `UserMenu` pour les utilisateurs connectés.
6. `apps/web/app/login/page.tsx` : Branchement du composant `LoginForm`.
7. `apps/web/app/register/page.tsx` : Branchement du composant `RegisterForm`.
8. `apps/web/app/dashboard/page.tsx` : Protection de la route via `ProtectedRoute`.
9. `docs/api/endpoints_v1.md` : Mise à jour de la documentation d'API.

---

## 3. Endpoints Implémentés & Testés

| Méthode | Endpoint | Protection | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Inscription avec validation du mot de passe (min 8 car., confirmation) et génération immédiate des tokens JWT |
| `POST` | `/api/v1/auth/login` | Public | Authentification email/password avec retour des tokens access/refresh et profil |
| `POST` | `/api/v1/auth/refresh` | Public | Renouvellement de l'access token via le refresh token |
| `POST` | `/api/v1/auth/logout` | Public/Auth | Clôture de session et révocation du refresh token |
| `GET` | `/api/v1/auth/me` | **Bearer JWT** | Récupération du profil de l'utilisateur authentifié |
| `PATCH` | `/api/v1/auth/me` | **Bearer JWT** | Mise à jour partielle du profil (prénom, nom, langue, avatar) |

---

## 4. Résultats des Tests et Validations

| Suite de tests / Contrôle | Commande | Résultat | Statut |
|---|---|---|---|
| **Inscription** | `pytest test_auth.py::test_user_registration_*` | Inscription nominale (201), rejet doublon email (400), rejet mot de passe divergent (400) | ✅ Validé |
| **Connexion** | `pytest test_auth.py::test_user_login_success` | Retourne 200, access/refresh tokens et user profile | ✅ Validé |
| **Mauvais mot de passe** | `pytest test_auth.py::test_user_login_wrong_password` | Rejet 400 avec message explicite | ✅ Validé |
| **Utilisateur désactivé** | `pytest test_auth.py::test_user_login_inactive_user` | Rejet de connexion 400 et rejet token 401 | ✅ Validé |
| **Token & Authentification** | `pytest test_auth.py::test_token_access_me_endpoint` | Accès autorisé avec Bearer Token, rejet 401 sans token | ✅ Validé |
| **Refresh Token** | `pytest test_auth.py::test_token_refresh` | Émission d'un nouvel access token | ✅ Validé |
| **Accès utilisateur / Profil** | `pytest test_auth.py::test_user_profile_update` | Modification prénom, nom, langue via PATCH /me | ✅ Validé |
| **Déconnexion** | `pytest test_auth.py::test_user_logout` | Déconnexion réussie et nettoyage de session | ✅ Validé |
| **Total Tests Backend** | `pytest apps/api` | **19/19 tests passés** en 0.97s | ✅ Validé |
| **Linter Python** | `ruff check apps/api` | `All checks passed!` | ✅ Validé |
| **Typage TypeScript** | `npm run typecheck` | 0 erreur TypeScript | ✅ Validé |
| **Build Next.js** | `npm run build` | 8 routes statiques compilées (`/`, `/login`, `/register`, `/profile`, `/dashboard`, etc.) | ✅ Validé |

---

## 5. Validation des Critères d'Acceptation

- [x] **Créer son compte** : formulaire `/register` fonctionnel, validation stricte, persistance sécurisée en base de données.
- [x] **Se connecter** : formulaire `/login` avec email/mot de passe, émission des JWT tokens.
- [x] **Rester authentifié** : persistance des tokens, rafraîchissement automatique en tâche de fond via `AuthProvider`.
- [x] **Récupérer son profil** : endpoint `GET /api/v1/auth/me` et page `/profile` protégée avec possibilité de mise à jour.
- [x] **Se déconnecter** : action `Se déconnecter` dans le menu utilisateur révoquant la session et nettoyant le cache local.
- [x] **Principe 1.1 respecté** : arrêt strict au terme du **Sprint 01**, sans commencer le **Sprint 02**.
