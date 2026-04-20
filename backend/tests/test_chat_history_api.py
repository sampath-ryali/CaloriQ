"""API tests for persistent chat history endpoints."""

from __future__ import annotations

import unittest
from uuid import uuid4
from unittest.mock import patch

from app import create_app
from config import TestingConfig
from models.analysis_result import AnalysisResult


class ChatHistoryApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

    def _register_user_and_token(self) -> tuple[str, str]:
        username = f"chatapi_{uuid4().hex[:10]}@example.com"
        password = "password123"

        response = self.client.post(
            "/api/auth/register",
            json={"username": username, "password": password},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        assert payload is not None
        return payload["access_token"], payload["user"]["id"]

    def test_chat_exchange_is_persisted_and_retrievable(self) -> None:
        token, user_id = self._register_user_and_token()
        headers = {"Authorization": f"Bearer {token}"}
        chat_id = f"chat-{uuid4().hex[:8]}"

        fake_result = AnalysisResult(
            image_id="image-test-001",
            question="Is this healthy?",
            answer="This looks moderately healthy.",
            confidence=0.91,
            insights=["Moderate calories"],
            source="rule_based",
            language="en",
        )

        with patch("routes.qa.AnalysisService.analyze", return_value=fake_result):
            ask_response = self.client.post(
                "/api/ask-question",
                json={
                    "image_id": "image-test-001",
                    "question": "Is this healthy?",
                    "language": "en",
                    "chat_id": chat_id,
                },
                headers=headers,
            )

        self.assertEqual(ask_response.status_code, 200)
        ask_payload = ask_response.get_json()
        assert ask_payload is not None
        self.assertEqual(ask_payload.get("chat_id"), chat_id)
        self.assertEqual(ask_payload.get("user_id"), user_id)

        chats_response = self.client.get("/api/chats", headers=headers)
        self.assertEqual(chats_response.status_code, 200)
        chats_payload = chats_response.get_json()
        assert chats_payload is not None
        chats = chats_payload.get("chats", [])
        self.assertTrue(any(chat.get("id") == chat_id for chat in chats))

        messages_response = self.client.get(f"/api/chats/{chat_id}/messages", headers=headers)
        self.assertEqual(messages_response.status_code, 200)
        messages_payload = messages_response.get_json()
        assert messages_payload is not None
        messages = messages_payload.get("messages", [])

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].get("role"), "user")
        self.assertEqual(messages[1].get("role"), "assistant")
        self.assertEqual(messages[1].get("content"), "This looks moderately healthy.")

    def test_user_cannot_read_another_users_chat_messages(self) -> None:
        owner_token, _owner_user_id = self._register_user_and_token()
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        intruder_token, _intruder_user_id = self._register_user_and_token()
        intruder_headers = {"Authorization": f"Bearer {intruder_token}"}
        chat_id = f"chat-{uuid4().hex[:8]}"

        fake_result = AnalysisResult(
            image_id="image-test-002",
            question="What is this?",
            answer="A nutrition label.",
            confidence=0.95,
            insights=["Detected nutrition label"],
            source="rule_based",
            language="en",
        )

        with patch("routes.qa.AnalysisService.analyze", return_value=fake_result):
            ask_response = self.client.post(
                "/api/ask-question",
                json={
                    "image_id": "image-test-002",
                    "question": "What is this?",
                    "language": "en",
                    "chat_id": chat_id,
                },
                headers=owner_headers,
            )
        self.assertEqual(ask_response.status_code, 200)

        denied_response = self.client.get(f"/api/chats/{chat_id}/messages", headers=intruder_headers)
        self.assertEqual(denied_response.status_code, 404)
        denied_payload = denied_response.get_json()
        assert denied_payload is not None
        self.assertEqual(denied_payload.get("error", {}).get("code"), "chat_not_found")


if __name__ == "__main__":
    unittest.main()
