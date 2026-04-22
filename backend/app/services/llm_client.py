"""
LLM Client — thin wrapper around any OpenAI-compatible API
that returns validated Pydantic objects.

The FlowEngine never talks to the LLM directly. It calls this client,
which handles API calls, JSON parsing, retries, and fallback.

Works with any OpenAI-compatible endpoint: UF Navigator (LiteLLM),
OpenAI, or any other proxy that implements the chat completions API.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.llm import LLMTurnResponse, RoutingSignal, TutorGesture, TutorExpression

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    """
    Wraps the validated LLM response with telemetry metadata.

    LLMTurnResponse is the LLM's contract (what it returns).
    LLMResult adds operational data the LLM doesn't know about:
    response time, token counts, which attempt succeeded.
    """
    response: LLMTurnResponse
    response_time_ms: int = 0
    token_usage: dict = field(default_factory=dict)  # {"prompt": N, "completion": N, "total": N}
    attempt_number: int = 1  # 1 = first try, 2 = repair, 3+ = retries


@runtime_checkable
class LLMClient(Protocol):
    """
    Abstract interface for any LLM provider.

    The FlowEngine depends on this protocol, not a concrete class.
    To swap providers, implement this interface and change the factory.
    """

    async def generate_response(
        self,
        messages: list[dict],
        system_prompt: str,
        stage_id: str,
    ) -> LLMResult:
        """
        Send a conversation to the LLM and get a validated response.

        Args:
            messages:      Chat history as list of {"role": ..., "content": ...}
            system_prompt: Full system prompt (from build_system_prompt)
            stage_id:      Current stage (for logging/fallback)

        Returns:
            LLMResult containing the validated response + telemetry.
        """
        ...


# Fallback templates (D1 responses, used when LLM is unavailable)

FALLBACK_RESPONSES = {
    "greeting": "Hey! I'm here to help you reflect on your robotics project. What would you like to talk about today?",
    "context_gathering": "Can you tell me more about what you're working on right now?",
    "problem_exploration": "What challenges are you running into?",
    "guided_reflection": "That's interesting — why do you think that might be happening?",
    "solution_brainstorm": "What are some approaches you could try?",
    "action_planning": "What's one concrete step you could take next?",
    "wrap_up": "Thanks for this conversation! You've done some great thinking today.",
}

DEFAULT_FALLBACK = "I'm here to help you reflect. Can you tell me more about what's on your mind?"


def _build_fallback(stage_id: str) -> LLMResult:
    """Build a safe fallback response when the LLM fails entirely."""
    return LLMResult(
        response=LLMTurnResponse(
            tutor_response=FALLBACK_RESPONSES.get(stage_id, DEFAULT_FALLBACK),
            stage_completed=False,
            routing_signal=RoutingSignal.STAY,
            tutor_gesture=TutorGesture.IDLE,
            tutor_expression=TutorExpression.NEUTRAL,
            reflection_data={"fallback": True, "reason": "llm_failure"},
        ),
        response_time_ms=0,
        token_usage={},
        attempt_number=0,  # 0 = fallback, never reached the LLM
    )


REPAIR_INSTRUCTION = (
    "Your previous response was not valid JSON. Please respond with ONLY "
    "a JSON object in the exact format specified in the system prompt. "
    "No markdown, no explanation, no code fences — just the raw JSON object."
)


class NavigatorClient:
    """
    LLM client for any OpenAI-compatible API (UF Navigator, OpenAI, etc.).

    Uses the OpenAI Python SDK pointed at the configured base URL.
    JSON mode is attempted first; if the endpoint doesn't support it,
    falls back to prompt engineering + markdown fence stripping.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int | None = None,
    ):
        self._api_key = api_key or settings.LLM_API_KEY
        self._base_url = base_url or settings.LLM_BASE_URL
        self._model = model or settings.LLM_MODEL
        self._max_retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES

        if not self._api_key:
            logger.warning("LLM_API_KEY is not set. LLM calls will use fallback responses.")

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        ) if self._api_key else None

    async def generate_response(
        self,
        messages: list[dict],
        system_prompt: str,
        stage_id: str,
    ) -> LLMResult:
        """
        Call the LLM and return a validated LLMResult.

        Retry strategy:
          1. First attempt with JSON mode
          2. If JSON parse/validation fails, retry with repair instruction
          3. If all retries fail, return deterministic fallback
        """
        if not self._client:
            logger.warning("No LLM client available, returning fallback.")
            return _build_fallback(stage_id)

        # Build the full message list: system + conversation history
        full_messages = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        # Attempt loop: initial + retries
        last_error = None
        start_time = time.monotonic()

        for attempt in range(1 + self._max_retries):
            try:
                if attempt > 0:
                    # Add repair instruction on retry attempts
                    logger.info(f"LLM retry attempt {attempt} for stage '{stage_id}'")
                    full_messages.append({
                        "role": "user",
                        "content": REPAIR_INSTRUCTION,
                    })

                # Try JSON mode first; fall back to plain if unsupported
                try:
                    completion = await self._client.chat.completions.create(
                        model=self._model,
                        messages=full_messages,
                        response_format={"type": "json_object"},
                        temperature=0.7,
                        max_tokens=1024,
                    )
                except Exception:
                    completion = await self._client.chat.completions.create(
                        model=self._model,
                        messages=full_messages,
                        temperature=0.7,
                        max_tokens=1024,
                    )

                raw_content = completion.choices[0].message.content
                if not raw_content:
                    raise ValueError("Empty response from LLM")

                # Strip markdown fences if the model wraps JSON in ```
                cleaned = raw_content.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    cleaned = "\n".join(lines)

                # Parse JSON and validate with Pydantic
                parsed = json.loads(cleaned)
                response = LLMTurnResponse(**parsed)

                elapsed_ms = int((time.monotonic() - start_time) * 1000)

                token_usage = {}
                if completion.usage:
                    token_usage = {
                        "prompt": completion.usage.prompt_tokens,
                        "completion": completion.usage.completion_tokens,
                        "total": completion.usage.total_tokens,
                    }

                if attempt > 0:
                    logger.info(f"LLM retry succeeded on attempt {attempt + 1}")

                return LLMResult(
                    response=response,
                    response_time_ms=elapsed_ms,
                    token_usage=token_usage,
                    attempt_number=attempt + 1,
                )

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"LLM returned invalid JSON on attempt {attempt + 1}: {e}")
            except (ValueError, TypeError) as e:
                last_error = e
                logger.warning(f"LLM response failed validation on attempt {attempt + 1}: {e}")
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error calling LLM on attempt {attempt + 1}: {e}")
                break

        # All attempts failed — return safe fallback
        logger.error(
            f"All LLM attempts failed for stage '{stage_id}'. "
            f"Last error: {last_error}. Returning fallback."
        )
        return _build_fallback(stage_id)


def get_llm_client() -> NavigatorClient:
    """Factory function to create the LLM client."""
    logger.info(f"Using LLM: {settings.LLM_MODEL} at {settings.LLM_BASE_URL}")
    return NavigatorClient()
