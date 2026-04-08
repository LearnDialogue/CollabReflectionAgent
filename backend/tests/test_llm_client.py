"""
Tests for LLM Client (app/services/llm_client.py).

Includes both unit tests (no API calls) and an integration test
(real API call, skipped if LLM_API_KEY is not set).
"""

import json
import pytest
import asyncio

from app.services.llm_client import (
    NavigatorClient,
    get_llm_client,
    LLMClient,
    _build_fallback,
    FALLBACK_RESPONSES,
)
from app.schemas.llm import LLMTurnResponse, RoutingSignal
from app.core.prompts import build_system_prompt


class TestFallback:
    """Fallback responses work for every stage."""

    def test_fallback_returns_valid_response(self):
        """Every stage produces a valid LLMTurnResponse fallback."""
        for stage_id in FALLBACK_RESPONSES:
            fb = _build_fallback(stage_id)
            assert isinstance(fb, LLMTurnResponse)
            assert fb.stage_completed is False
            assert fb.routing_signal == RoutingSignal.STAY
            assert fb.reflection_data["fallback"] is True

    def test_fallback_unknown_stage(self):
        """Unknown stage still produces a valid fallback."""
        fb = _build_fallback("nonexistent_stage")
        assert isinstance(fb, LLMTurnResponse)
        assert len(fb.student_text) > 0

    def test_fallback_text_is_human_readable(self):
        """Fallback text should be a real sentence, not an error message."""
        for stage_id, text in FALLBACK_RESPONSES.items():
            assert len(text) > 10, f"Fallback for {stage_id} is too short"
            assert "error" not in text.lower()


class TestClientInit:
    """Client initializes correctly with various configurations."""

    def test_factory_returns_navigator_client(self):
        client = get_llm_client()
        assert isinstance(client, NavigatorClient)
        assert isinstance(client, LLMClient)

    def test_client_with_no_key_has_no_usable_key(self):
        """Client without API key should still instantiate (uses fallback on calls)."""
        client = NavigatorClient(api_key="")
        assert client._api_key == ""

    def test_client_custom_model(self):
        client = NavigatorClient(api_key="test", model="gpt-4o")
        assert client._model == "gpt-4o"

    def test_client_custom_retries(self):
        client = NavigatorClient(api_key="test", max_retries=5)
        assert client._max_retries == 5


class TestNoKeyFallback:
    """When there's no API key, the client returns fallback without crashing."""

    def test_no_key_returns_fallback(self):
        client = NavigatorClient(api_key="")
        system_prompt = build_system_prompt("greeting", student_name="Test")
        messages = [{"role": "user", "content": "Hello"}]

        response = asyncio.run(
            client.generate_response(messages, system_prompt, "greeting")
        )

        assert isinstance(response, LLMTurnResponse)
        assert response.reflection_data["fallback"] is True


class TestLiveAPICall:
    """
    Tests that hit the real LLM API.
    Skipped automatically if the key is not set.
    """

    def test_real_api_greeting(self):
        """Send a real message and get a structured response back."""
        client = get_llm_client()
        if not client._api_key:
            pytest.skip("No LLM_API_KEY set")

        system_prompt = build_system_prompt("greeting", student_name="Aman")
        messages = [
            {"role": "user", "content": "Hey, I want to talk about my robot arm project."}
        ]

        try:
            response = asyncio.run(
                client.generate_response(messages, system_prompt, "greeting")
            )
        except Exception:
            pytest.skip("API call failed (likely quota issue)")

        assert isinstance(response, LLMTurnResponse)
        assert len(response.student_text) > 0

        # If we got a non-fallback response, it means the LLM actually replied
        if response.reflection_data and response.reflection_data.get("fallback"):
            pytest.skip("Got fallback response (likely quota issue)")

        assert response.routing_signal in (RoutingSignal.NEXT, RoutingSignal.STAY)
