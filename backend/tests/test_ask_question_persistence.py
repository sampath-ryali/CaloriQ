"""Tests for ask-question persistence behavior on analysis failures."""

from __future__ import annotations

import unittest
from uuid import uuid4
from unittest.mock import patch

from app import create_app
from config import TestingConfig
from services.analysis_service import AnalysisServiceError


class AskQuestionPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

    def _register_user_and_token(self) -> tuple[str, str]:
        username = f"aqpersist_{uuid4().hex[:10]}@example.com"
        password = "password123"

        response = self.client.post(
            "/api/auth/register",
            json={"username": username, "password": password},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        assert payload is not None
        return payload["access_token"], payload["user"]["id"]

    def test_failed_analysis_still_creates_chat_history(self) -> None:
        token, _user_id = self._register_user_and_token()
        headers = {"Authorization": f"Bearer {token}"}
        chat_id = f"chat-{uuid4().hex[:8]}"

        with patch("routes.qa.AnalysisService.analyze", side_effect=AnalysisServiceError("analysis failed")):
            response = self.client.post(
                "/api/ask-question",
                json={
                    "image_id": "image-test-003",
                    "question": "is it healthy?",
                    "language": "en",
                    "chat_id": chat_id,
                },
                headers=headers,
            )

        self.assertEqual(response.status_code, 422)

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


if __name__ == "__main__":
    unittest.main()
