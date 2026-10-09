import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.chat.models import ChatSession
from apps.organizations.models import Organization, OrganizationMember

User = get_user_model()


@pytest.fixture
def chat_setup(db):
    user = User.objects.create_user(
        email="test_sse_user@example.com",
        password="password123",
    )
    org = Organization.objects.create(name="SSE Test Org", slug="sse-test-org")
    OrganizationMember.objects.create(
        user=user,
        organization=org,
        role="teacher",
    )
    session = ChatSession.objects.create(
        user=user,
        organization=org,
        title="SSE Test Session",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return {
        "user": user,
        "org": org,
        "session": session,
        "client": client,
    }


@pytest.mark.django_db(transaction=True)
class TestSSEStreamingHardening:
    """Validate Phase 15.5 SSE streaming resilience, headers, and concurrent non-blocking execution."""

    def test_sse_streaming_response_headers_and_contract(self, chat_setup):
        """Verify headers required for SSE (X-Accel-Buffering, Cache-Control, text/event-stream)."""
        client = chat_setup["client"]
        session = chat_setup["session"]

        payload = {
            "content": "Bonjour, explique-moi le cycle de l'eau.",
            "stream": True,
        }

        response = client.post(
            f"/api/v1/chat/sessions/{session.id}/messages/",
            payload,
            format="json",
        )

        assert response.status_code == 200
        assert "text/event-stream" in response["Content-Type"]
        assert response["Cache-Control"] == "no-cache"
        assert response["X-Accel-Buffering"] == "no"

        # Consume the streaming response generator
        chunks = list(response.streaming_content)
        assert len(chunks) >= 2  # start and token/done chunks
        full_text = b"".join(chunks).decode("utf-8")
        assert "data: " in full_text
        assert '"type": "start"' in full_text or '"type":' in full_text

    def test_concurrent_sse_streams_do_not_block_standard_api_requests(self, chat_setup):
        """Simulate concurrent slow SSE streams and verify that regular API calls remain immediately responsive."""
        session = chat_setup["session"]

        def slow_generator(*args, **kwargs):
            yield 'data: {"type": "start"}\n\n'
            for i in range(3):
                time.sleep(0.04)
                yield f'data: {{"type": "token", "content": "chunk_{i}"}}\n\n'
            yield 'data: {"type": "done"}\n\n'

        def simulated_slow_stream(prompt_idx):
            with patch("apps.chat.views.AITutorService.process_message_stream", side_effect=slow_generator):
                sub_client = APIClient()
                sub_client.force_authenticate(user=chat_setup["user"])
                res = sub_client.post(
                    f"/api/v1/chat/sessions/{session.id}/messages/",
                    {"content": f"Slow streaming question {prompt_idx}", "stream": True},
                    format="json",
                )
                assert res.status_code == 200
                content = list(res.streaming_content)
                return len(content)

        def standard_api_request(req_idx):
            sub_client = APIClient()
            sub_client.force_authenticate(user=chat_setup["user"])
            t0 = time.time()
            res = sub_client.get("/api/v1/chat/commands/")
            duration = time.time() - t0
            assert res.status_code == 200
            data = res.json()
            assert "commands" in data
            return duration

        with ThreadPoolExecutor(max_workers=8) as executor:
            # Launch 3 slow streaming requests concurrently
            stream_futures = [executor.submit(simulated_slow_stream, i) for i in range(3)]
            time.sleep(0.02)  # Let streams start executing

            # In parallel, execute standard API requests
            api_futures = [executor.submit(standard_api_request, j) for j in range(5)]

            # Check that regular API requests returned quickly without waiting for streams
            api_durations = [f.result() for f in api_futures]
            for dur in api_durations:
                assert dur < 0.25, f"Standard API took {dur}s, expected < 0.25s (blocked by SSE)"

            # Ensure all slow streams completed successfully as well
            stream_results = [f.result() for f in stream_futures]
            for res_count in stream_results:
                assert res_count > 0
