"""
Tests for LLM response schema (app/schemas/llm.py).

Validates that the Pydantic model correctly accepts good JSON
and rejects malformed / incomplete JSON from the LLM.
"""

import json
import pytest
from pydantic import ValidationError

from app.schemas.llm import LLMTurnResponse, RoutingSignal, TutorGesture, TutorExpression


class TestValidPayloads:
    """LLMTurnResponse should parse valid JSON without error."""

    def test_minimal_valid(self):
        """Bare minimum: text + completed + signal, no reflection_data."""
        data = {
            "tutor_response": "That sounds like a tough situation.",
            "stage_completed": False,
            "routing_signal": "STAY",
        }
        resp = LLMTurnResponse(**data)
        assert resp.tutor_response == "That sounds like a tough situation."
        assert resp.stage_completed is False
        assert resp.routing_signal == RoutingSignal.STAY
        assert resp.reflection_data is None

    def test_full_valid_with_reflection(self):
        """All fields present, including reflection_data, tutor_gesture, and tutor_expression."""
        data = {
            "tutor_response": "Let's move on to brainstorming solutions.",
            "stage_completed": True,
            "routing_signal": "NEXT",
            "tutor_gesture": "keepGoing",
            "tutor_expression": "warmSmile",
            "reflection_data": {
                "emotional_tone": "frustrated",
                "conflict_detected": False,
                "engagement_level": "high",
            },
        }
        resp = LLMTurnResponse(**data)
        assert resp.stage_completed is True
        assert resp.routing_signal == RoutingSignal.NEXT
        assert resp.tutor_gesture == TutorGesture.KEEP_GOING
        assert resp.tutor_expression == TutorExpression.WARM_SMILE
        assert resp.reflection_data["emotional_tone"] == "frustrated"
        assert resp.reflection_data["conflict_detected"] is False

    def test_reflection_data_explicit_none(self):
        """reflection_data can be explicitly null."""
        data = {
            "tutor_response": "Hello!",
            "stage_completed": False,
            "routing_signal": "STAY",
            "reflection_data": None,
        }
        resp = LLMTurnResponse(**data)
        assert resp.reflection_data is None

    def test_parse_from_json_string(self):
        """Simulate the real flow: parse raw JSON string → dict → model."""
        raw = json.dumps({
            "tutor_response": "Tell me more about that.",
            "stage_completed": False,
            "routing_signal": "STAY",
        })
        parsed = json.loads(raw)
        resp = LLMTurnResponse(**parsed)
        assert resp.tutor_response == "Tell me more about that."

    def test_routing_signal_enum_values(self):
        """Both enum values are accepted."""
        for signal in ["NEXT", "STAY"]:
            resp = LLMTurnResponse(
                tutor_response="test",
                stage_completed=False,
                routing_signal=signal,
            )
            assert resp.routing_signal.value == signal

    def test_tutor_gesture_defaults_to_idle(self):
        """tutor_gesture defaults to idle when omitted."""
        resp = LLMTurnResponse(
            tutor_response="test",
            stage_completed=False,
            routing_signal="STAY",
        )
        assert resp.tutor_gesture == TutorGesture.IDLE

    def test_tutor_gesture_valid_values(self):
        """All known gesture values are accepted."""
        for gesture in [
            "celebrate", "concerned", "idle", "keepGoing",
            "leanInHandOut", "scratchHead", "singleWave", "thinking",
        ]:
            resp = LLMTurnResponse(
                tutor_response="test",
                stage_completed=False,
                routing_signal="STAY",
                tutor_gesture=gesture,
            )
            assert resp.tutor_gesture.value == gesture

    def test_tutor_gesture_unknown_falls_back_to_idle(self):
        """Unrecognized gesture string falls back to idle, not a crash."""
        resp = LLMTurnResponse(
            tutor_response="test",
            stage_completed=False,
            routing_signal="STAY",
            tutor_gesture="dab",
        )
        assert resp.tutor_gesture == TutorGesture.IDLE

    def test_tutor_expression_defaults_to_neutral(self):
        """tutor_expression defaults to neutral when omitted."""
        resp = LLMTurnResponse(
            tutor_response="test",
            stage_completed=False,
            routing_signal="STAY",
        )
        assert resp.tutor_expression == TutorExpression.NEUTRAL

    def test_tutor_expression_valid_values(self):
        """All known expression values are accepted."""
        for expr in [
            "neutral", "veryExcited", "warmSmile", "concerned",
            "contemplative", "deepThought", "nod",
        ]:
            resp = LLMTurnResponse(
                tutor_response="test",
                stage_completed=False,
                routing_signal="STAY",
                tutor_expression=expr,
            )
            assert resp.tutor_expression.value == expr

    def test_tutor_expression_unknown_falls_back_to_neutral(self):
        """Unrecognized expression string falls back to neutral, not a crash."""
        resp = LLMTurnResponse(
            tutor_response="test",
            stage_completed=False,
            routing_signal="STAY",
            tutor_expression="angry",
        )
        assert resp.tutor_expression == TutorExpression.NEUTRAL


class TestInvalidPayloads:
    """LLMTurnResponse should reject malformed data with ValidationError."""

    def test_missing_tutor_response(self):
        """tutor_response is required."""
        with pytest.raises(ValidationError) as exc_info:
            LLMTurnResponse(
                stage_completed=False,
                routing_signal="STAY",
            )
        assert "tutor_response" in str(exc_info.value)

    def test_empty_tutor_response(self):
        """tutor_response must have at least 1 character."""
        with pytest.raises(ValidationError):
            LLMTurnResponse(
                tutor_response="",
                stage_completed=False,
                routing_signal="STAY",
            )

    def test_missing_stage_completed(self):
        """stage_completed is required."""
        with pytest.raises(ValidationError) as exc_info:
            LLMTurnResponse(
                tutor_response="Hello",
                routing_signal="STAY",
            )
        assert "stage_completed" in str(exc_info.value)

    def test_missing_routing_signal(self):
        """routing_signal is required."""
        with pytest.raises(ValidationError) as exc_info:
            LLMTurnResponse(
                tutor_response="Hello",
                stage_completed=False,
            )
        assert "routing_signal" in str(exc_info.value)

    def test_invalid_routing_signal(self):
        """routing_signal must be NEXT or STAY."""
        with pytest.raises(ValidationError):
            LLMTurnResponse(
                tutor_response="Hello",
                stage_completed=False,
                routing_signal="JUMP_BACK",
            )

    def test_completely_empty_dict(self):
        """Empty dict should fail."""
        with pytest.raises(ValidationError):
            LLMTurnResponse(**{})

    def test_bad_json_string(self):
        """Malformed JSON string should fail at json.loads, not Pydantic."""
        with pytest.raises(json.JSONDecodeError):
            json.loads("not valid json {{{")

    def test_tutor_response_wrong_type(self):
        """tutor_response must be a string."""
        with pytest.raises(ValidationError):
            LLMTurnResponse(
                tutor_response=12345,
                stage_completed=False,
                routing_signal="STAY",
            )
