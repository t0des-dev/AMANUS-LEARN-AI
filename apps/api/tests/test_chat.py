import json
import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.ai.services import DeterministicEmbeddingProvider, get_embedding_provider
from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.chat.services.pedagogical_commands import (
    PEDAGOGICAL_COMMANDS,
    detect_pedagogical_command,
    get_command_instruction,
)
from apps.documents.models import Document, DocumentStatus
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.organizations.models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


class PedagogicalCommandsUnitTests(APITestCase):
    """Unit tests for the Pedagogical Commands parsing and prompt instructions."""

    def test_all_eight_pedagogical_commands_detection(self):
        cases = [
            ("Explique-moi le fonctionnement des transformateurs", "EXPLAIN", "le fonctionnement des transformateurs"),
            ("Explique l'algorithme de descente de gradient", "EXPLAIN", "l'algorithme de descente de gradient"),
            ("/explique les tenseurs", "EXPLAIN", "les tenseurs"),
            ("Simplifie le concept de rétropropagation", "SIMPLIFY", "le concept de rétropropagation"),
            ("/simplifie l'entropie croisée", "SIMPLIFY", "l'entropie croisée"),
            ("Résume le chapitre 3", "SUMMARY", "le chapitre 3"),
            ("Fais un résumé des notions clés", "SUMMARY", "des notions clés"),
            ("/resume l'introduction", "SUMMARY", "l'introduction"),
            ("Donne un exemple d'application des CNN", "EXAMPLE", "application des CNN"),
            ("Exemple de fonction d'activation", "EXAMPLE", "fonction d'activation"),
            ("/exemple d'auto-encodeur", "EXAMPLE", "d'auto-encodeur"),
            ("Interroge-moi sur les mécanismes d'attention", "QUIZ", "les mécanismes d'attention"),
            ("Pose-moi des questions sur le surapprentissage", "QUIZ", "le surapprentissage"),
            ("/interroge le réseau résiduel", "QUIZ", "le réseau résiduel"),
            ("Fais-moi réviser les principes de normalisation", "REVISION", "les principes de normalisation"),
            ("Révision de la couche softmax", "REVISION", "la couche softmax"),
            ("/revision les pondérations", "REVISION", "les pondérations"),
            ("Compare l'optimiseur Adam et la descente SGD", "COMPARE", "l'optimiseur Adam et la descente SGD"),
            ("/compare RNN et LSTM", "COMPARE", "RNN et LSTM"),
            ("Définis la fonction de coût", "DEFINE", "la fonction de coût"),
            ("Donne la définition de la régularisation L2", "DEFINE", "la régularisation L2"),
            ("/definis les hyperparamètres", "DEFINE", "les hyperparamètres"),
        ]

        for text, expected_cmd, expected_clean in cases:
            cmd, clean_query = detect_pedagogical_command(text)
            self.assertEqual(cmd, expected_cmd, f"Failed command detection for: '{text}'")
            self.assertIn(expected_clean, clean_query, f"Failed clean query for: '{text}'")

    def test_explicit_command_parameter_override(self):
        cmd, clean = detect_pedagogical_command("Quel est ce principe ?", explicit_command="SIMPLIFY")
        self.assertEqual(cmd, "SIMPLIFY")
        self.assertEqual(clean, "Quel est ce principe ?")

    def test_instructions_exist_for_all_commands(self):
        expected_keys = ["EXPLAIN", "SIMPLIFY", "SUMMARY", "EXAMPLE", "QUIZ", "REVISION", "COMPARE", "DEFINE"]
        for key in expected_keys:
            self.assertIn(key, PEDAGOGICAL_COMMANDS)
            instruction = get_command_instruction(key)
            self.assertTrue(len(instruction) > 20)


class ChatSessionAndRAGIntegrationTests(APITestCase):
    """End-to-end integration tests for ChatSession, ChatMessage, RAG retrieval, citations, permissions and streaming."""

    def setUp(self):
        self.embedding_provider = DeterministicEmbeddingProvider(dimensions=1536)

        # Organization Alpha & Alice (Owner)
        self.user_a = User.objects.create_user(
            email="alice@alpha-learn.com",
            password="PasswordAlpha123!",
            first_name="Alice",
        )
        self.org_a = Organization.objects.create(name="Alpha Edu Corp")
        self.member_a = OrganizationMember.objects.create(
            organization=self.org_a,
            user=self.user_a,
            role=RoleChoices.OWNER,
        )

        # Document and Chunks for Org Alpha
        self.doc_a = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Manuel d'Intelligence Artificielle Alpha",
            file_name="manuel_alpha.pdf",
            file_type="pdf",
            file_size=2048,
            storage_key="docs/alpha.pdf",
            status=DocumentStatus.READY,
        )
        self.page_a = DocumentPage.objects.create(
            document=self.doc_a,
            page_number=4,
            text="Chapitre 2 : Mécanismes d'attention\nL'auto-attention pondère les relations entre tokens.",
            metadata={"chapter": "Chapitre 2 : Mécanismes d'attention", "section": "2.1 Auto-Attention"},
        )
        self.chunk_a = DocumentChunk.objects.create(
            document=self.doc_a,
            page=self.page_a,
            chunk_index=0,
            content="L'auto-attention permet de calculer des poids de pertinence pour chaque paire de mots dans la phrase.",
            token_count=18,
            metadata={
                "document_id": str(self.doc_a.id),
                "document_title": self.doc_a.title,
                "page_number": 4,
                "chapter": "Chapitre 2 : Mécanismes d'attention",
                "section": "2.1 Auto-Attention",
            },
            embedding=self.embedding_provider.embed_text(
                "L'auto-attention permet de calculer des poids de pertinence pour chaque paire de mots dans la phrase."
            ),
        )

        # Organization Beta & Bob (Owner) - isolated tenant
        self.user_b = User.objects.create_user(
            email="bob@beta-learn.com",
            password="PasswordBeta123!",
            first_name="Bob",
        )
        self.org_b = Organization.objects.create(name="Beta Edu Corp")
        self.member_b = OrganizationMember.objects.create(
            organization=self.org_b,
            user=self.user_b,
            role=RoleChoices.OWNER,
        )
        self.doc_b = Document.objects.create(
            organization=self.org_b,
            owner=self.user_b,
            title="Secrets Bancaires Beta",
            file_name="secrets_beta.pdf",
            file_type="pdf",
            file_size=1024,
            storage_key="docs/beta.pdf",
            status=DocumentStatus.READY,
        )
        self.page_b = DocumentPage.objects.create(
            document=self.doc_b,
            page_number=1,
            text="Données financières confidentielles de l'organisation Beta.",
            metadata={"chapter": "Confidentiel", "section": "Comptes"},
        )
        self.chunk_b = DocumentChunk.objects.create(
            document=self.doc_b,
            page=self.page_b,
            chunk_index=0,
            content="Comptes bancaires numérotés et actifs suisses hautement sécurisés de l'organisation Beta.",
            token_count=15,
            metadata={
                "document_id": str(self.doc_b.id),
                "document_title": self.doc_b.title,
                "page_number": 1,
            },
            embedding=self.embedding_provider.embed_text(
                "Comptes bancaires numérotés et actifs suisses hautement sécurisés de l'organisation Beta."
            ),
        )

        # JWT Tokens
        self.token_a = str(RefreshToken.for_user(self.user_a).access_token)
        self.token_b = str(RefreshToken.for_user(self.user_b).access_token)

    def _auth_a(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")

    def _auth_b(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")

    def test_pedagogical_commands_list_endpoint(self):
        self._auth_a()
        url = reverse("v1:chat:commands")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        commands = response.data["commands"]
        self.assertEqual(len(commands), 8)
        codes = [c["code"] for c in commands]
        for expected in ["EXPLAIN", "SIMPLIFY", "SUMMARY", "EXAMPLE", "QUIZ", "REVISION", "COMPARE", "DEFINE"]:
            self.assertIn(expected, codes)

    def test_create_and_list_chat_sessions(self):
        self._auth_a()
        url = reverse("v1:chat:session-list-create")

        # 1. Create a session scoped to doc_a
        payload = {
            "title": "Session Révision Attention",
            "organization_id": str(self.org_a.id),
            "document_id": str(self.doc_a.id),
        }
        res_create = self.client.post(url, payload, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        session_id = res_create.data["id"]
        self.assertEqual(res_create.data["title"], "Session Révision Attention")
        self.assertEqual(res_create.data["document_id"], str(self.doc_a.id))

        # 2. List sessions
        res_list = self.client.get(url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        # Should contain the newly created session
        results = res_list.data if isinstance(res_list.data, list) else res_list.data.get("results", [])
        self.assertTrue(any(s["id"] == session_id for s in results))

        # 3. Retrieve session detail
        url_detail = reverse("v1:chat:session-detail", kwargs={"id": session_id})
        res_detail = self.client.get(url_detail)
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data["document"]["id"], str(self.doc_a.id))
        self.assertEqual(len(res_detail.data["messages"]), 0)

    def test_multi_tenant_and_user_isolation_on_sessions(self):
        self._auth_a()
        url = reverse("v1:chat:session-list-create")
        payload = {"title": "Session Secrète Alice"}
        res = self.client.post(url, payload, format="json")
        alice_session_id = res.data["id"]

        # Bob from Tenant B tries to view Alice's session
        self._auth_b()
        url_detail = reverse("v1:chat:session-detail", kwargs={"id": alice_session_id})
        res_bob = self.client.get(url_detail)
        self.assertEqual(res_bob.status_code, status.HTTP_404_NOT_FOUND)

        # Bob cannot send a message to Alice's session
        url_msg = reverse("v1:chat:session-messages", kwargs={"id": alice_session_id})
        res_bob_msg = self.client.post(url_msg, {"content": "Coucou Alice"}, format="json")
        self.assertEqual(res_bob_msg.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_bind_document_from_another_organization(self):
        self._auth_a()
        url = reverse("v1:chat:session-list-create")
        # Alice tries to bind Bob's document (from Org B)
        payload = {
            "title": "Tentative intrusion",
            "organization_id": str(self.org_a.id),
            "document_id": str(self.doc_b.id),
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("document_id", res.data)

    def test_chat_message_sync_rag_and_citations(self):
        """Tests sending a message with synchronous RAG retrieval, citations provenance, and command detection."""
        self._auth_a()
        # Create session
        session = ChatSession.objects.create(
            organization=self.org_a,
            user=self.user_a,
            document=self.doc_a,
            title="Session IA",
        )

        url = reverse("v1:chat:session-messages", kwargs={"id": session.id})
        payload = {
            "content": "Explique-moi comment fonctionne l'auto-attention et les poids de pertinence",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.data
        self.assertIn("user_message", data)
        self.assertIn("assistant_message", data)

        # User message verification
        user_msg = data["user_message"]
        self.assertEqual(user_msg["role"], "user")
        self.assertEqual(user_msg["command"], "EXPLAIN")
        self.assertIn("auto-attention", user_msg["content"])

        # Assistant message verification
        assistant_msg = data["assistant_message"]
        self.assertEqual(assistant_msg["role"], "assistant")
        self.assertEqual(assistant_msg["command"], "EXPLAIN")
        self.assertTrue(len(assistant_msg["content"]) > 10)

        # Citations verification
        sources = assistant_msg["sources"]
        self.assertGreater(len(sources), 0)
        first_source = sources[0]
        self.assertEqual(first_source["citation_id"], 1)
        self.assertEqual(first_source["document_title"], "Manuel d'Intelligence Artificielle Alpha")
        self.assertEqual(first_source["document_id"], str(self.doc_a.id))
        self.assertEqual(first_source["page"], 4)
        self.assertIn("auto-attention", first_source["snippet"].lower())

        # Verify DB storage
        self.assertEqual(session.messages.count(), 2)

    def test_streaming_sse_endpoint(self):
        """Tests sending a message with stream=True returning Server-Sent Events."""
        self._auth_a()
        session = ChatSession.objects.create(
            organization=self.org_a,
            user=self.user_a,
            document=self.doc_a,
            title="Nouvelle session pédagogique",
        )

        url = reverse("v1:chat:session-messages", kwargs={"id": session.id})
        payload = {
            "content": "Simplifie le mécanisme d'attention",
            "stream": True,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response["Content-Type"].startswith("text/event-stream"))

        # Consume streaming generator
        raw_events = b"".join(response.streaming_content).decode("utf-8")
        lines = [line.strip() for line in raw_events.split("\n") if line.startswith("data: ")]
        self.assertGreater(len(lines), 0)

        events = [json.loads(line[6:]) for line in lines]
        event_types = [e["type"] for e in events]

        self.assertIn("start", event_types)
        self.assertIn("token", event_types)
        self.assertIn("done", event_types)

        done_event = next(e for e in events if e["type"] == "done")
        self.assertEqual(done_event["command"], "SIMPLIFY")
        self.assertGreater(len(done_event["sources"]), 0)
        self.assertTrue(len(done_event["content"]) > 0)

        # Verify messages are saved in database
        self.assertEqual(session.messages.count(), 2)
        saved_assistant = session.messages.filter(role=MessageRole.ASSISTANT).first()
        self.assertIsNotNone(saved_assistant)
        self.assertEqual(saved_assistant.command, "SIMPLIFY")
        self.assertEqual(len(saved_assistant.sources), len(done_event["sources"]))

    def test_document_scoping_and_cross_tenant_isolation_in_chat(self):
        """Verifies that asking about Beta's secret data from Alpha never returns Beta documents."""
        self._auth_a()
        session = ChatSession.objects.create(
            organization=self.org_a,
            user=self.user_a,
            title="Tentative d'accès cross-tenant",
        )

        url = reverse("v1:chat:session-messages", kwargs={"id": session.id})
        payload = {
            "content": "Quels sont les comptes bancaires suisses secrets ?",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        sources = response.data["assistant_message"]["sources"]
        # Must NOT contain any citations from doc_b or Org B
        for s in sources:
            self.assertNotEqual(s["document_id"], str(self.doc_b.id))
            self.assertNotEqual(s["document_title"], "Secrets Bancaires Beta")

    def test_pedagogical_commands_variations_and_provenance(self):
        """Verifies diverse pedagogical commands: Résume, Donne un exemple, Interroge-moi, Révision, Compare, Définis."""
        self._auth_a()
        session = ChatSession.objects.create(
            organization=self.org_a,
            user=self.user_a,
            document=self.doc_a,
            title="Session Pédagogique Multiple",
        )

        test_prompts = [
            ("Résume les notions du cours", "SUMMARY"),
            ("Donne un exemple pratique", "EXAMPLE"),
            ("Interroge-moi sur les concepts", "QUIZ"),
            ("Fais-moi réviser la théorie", "REVISION"),
            ("Compare l'attention et les réseaux convolutifs", "COMPARE"),
            ("Définis l'auto-attention", "DEFINE"),
        ]

        url = reverse("v1:chat:session-messages", kwargs={"id": session.id})
        for prompt_text, expected_cmd in test_prompts:
            res = self.client.post(url, {"content": prompt_text}, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertEqual(res.data["user_message"]["command"], expected_cmd)
            self.assertEqual(res.data["assistant_message"]["command"], expected_cmd)
            self.assertGreater(len(res.data["assistant_message"]["sources"]), 0)
