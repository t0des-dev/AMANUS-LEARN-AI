from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthenticationAPITests(APITestCase):
    """Complete test suite for Sprint 01 Authentication endpoints."""

    def setUp(self):
        self.register_url = reverse("v1:auth-register")
        self.login_url = reverse("v1:auth-login")
        self.refresh_url = reverse("v1:auth-refresh")
        self.logout_url = reverse("v1:auth-logout")
        self.me_url = reverse("v1:auth-me")

        self.user_email = "test.user@amanus.ai"
        self.user_password = "SuperSecurePassword123!"
        self.user = User.objects.create_user(
            email=self.user_email,
            password=self.user_password,
            first_name="Alice",
            last_name="Dupont",
            language="fr",
        )

    def test_user_registration_success(self):
        """Tester l'inscription d'un nouvel utilisateur."""
        payload = {
            "email": "new.learner@amanus.ai",
            "password": "StrongPassword2026!",
            "password_confirm": "StrongPassword2026!",
            "first_name": "Bob",
            "last_name": "Martin",
            "language": "fr",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "new.learner@amanus.ai")
        self.assertEqual(response.data["user"]["first_name"], "Bob")
        self.assertTrue(User.objects.filter(email="new.learner@amanus.ai").exists())

    def test_user_registration_duplicate_email(self):
        """Tester l'inscription avec un email déjà existant (rejet 400)."""
        payload = {
            "email": self.user_email,
            "password": "StrongPassword2026!",
            "password_confirm": "StrongPassword2026!",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_registration_password_mismatch(self):
        """Tester l'inscription avec mots de passe divergents."""
        payload = {
            "email": "mismatch@amanus.ai",
            "password": "StrongPassword2026!",
            "password_confirm": "DifferentPassword2026!",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """Tester la connexion réussie avec identifiants valides."""
        payload = {
            "email": self.user_email,
            "password": self.user_password,
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.user_email)

    def test_user_login_wrong_password(self):
        """Tester la connexion avec un mauvais mot de passe."""
        payload = {
            "email": self.user_email,
            "password": "WrongPassword!",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access", response.data)

    def test_user_login_inactive_user(self):
        """Tester qu'un utilisateur désactivé ne peut pas se connecter."""
        inactive_user = User.objects.create_user(
            email="inactive@amanus.ai",
            password="StrongPassword2026!",
            is_active=False,
        )
        payload = {
            "email": inactive_user.email,
            "password": "StrongPassword2026!",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_token_access_me_endpoint(self):
        """Tester l'accès au profil utilisateur via Bearer Token."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_email)
        self.assertEqual(response.data["first_name"], "Alice")

    def test_access_me_unauthorized(self):
        """Tester le refus d'accès sans token (401 Unauthorized)."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Tester le rafraîchissement d'un token via le endpoint refresh."""
        refresh = RefreshToken.for_user(self.user)
        payload = {"refresh": str(refresh)}
        response = self.client.post(self.refresh_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_user_profile_update(self):
        """Tester la mise à jour partielle du profil (PATCH /me)."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        update_payload = {
            "first_name": "Alicia",
            "last_name": "Martin-Dupont",
            "language": "en",
        }
        response = self.client.patch(self.me_url, update_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Alicia")
        self.assertEqual(response.data["last_name"], "Martin-Dupont")
        self.assertEqual(response.data["language"], "en")

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alicia")
        self.assertEqual(self.user.language, "en")

    def test_inactive_user_token_rejected(self):
        """Tester qu'un token appartenant à un utilisateur désactivé est rejeté."""
        self.user.is_active = False
        self.user.save()

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_logout(self):
        """Tester la déconnexion et révocation de session."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        payload = {"refresh": str(refresh)}
        response = self.client.post(self.logout_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Déconnexion réussie."})

    def test_invalid_bearer_token_rejected(self):
        """Vérifier qu'un token JWT malformé ou invalide est rejeté avec un code 401."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token-value-xyz")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tampered_token_rejected(self):
        """Vérifier qu'un token altéré est immédiatement rejeté."""
        refresh = RefreshToken.for_user(self.user)
        valid_token = str(refresh.access_token)
        tampered_token = valid_token[:-4] + "fake"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tampered_token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_cookie_cannot_bypass_jwt_auth(self):
        """Garantir que l'API DRF rejette les sessions sans JWT Bearer (stateless JWT)."""
        # Connecter via session standard Django sans header Authorization
        self.client.force_login(self.user)
        self.client.credentials()  # Aucun header Bearer
        response = self.client.get(self.me_url)
        # Puisque SessionAuthentication est retiré de DRF, l'accès doit être 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_drf_uses_strictly_jwt_authentication(self):
        """Vérifier que DRF est configuré pour JWT exclusivement afin d'éviter les failles CSRF."""
        from django.conf import settings
        from rest_framework_simplejwt.authentication import JWTAuthentication

        auth_classes = settings.REST_FRAMEWORK.get("DEFAULT_AUTHENTICATION_CLASSES", [])
        self.assertEqual(len(auth_classes), 1)
        self.assertEqual(auth_classes[0], "rest_framework_simplejwt.authentication.JWTAuthentication")
