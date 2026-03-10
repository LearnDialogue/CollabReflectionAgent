"""
Session Evaluator — post-session analysis via a single LLM call.

When a session completes, this service compiles the full conversation
transcript with all per-turn metadata, sends it to the LLM with a
strict evaluation prompt, and returns structured JSON analysis.

This is a separate call from the per-turn conversation. It runs once
per completed session and uses the full context window.
"""

import json
import logging
import time
from typing import Optional

from app.core.config import settings
from app.core.prompts import STAGE_REGISTRY, build_evaluation_prompt
from app.services.llm_client import OpenAIClient

logger = logging.getLogger(__name__)


async def evaluate_session(
    messages: list[dict],
    model: Optional[str] = None,
) -> Optional[dict]:
    """
    Run post-session evaluation on a completed conversation.

    Args:
        messages: List of message dicts with keys:
                  role, content, stage_id, llm_metadata, created_at
        model:    Override model (e.g. use gpt-4o for higher quality eval).
                  Defaults to the configured OPENAI_MODEL.

    Returns:
        Parsed evaluation JSON dict, or None if the call fails.
    """
    if not settings.OPENAI_API_KEY and not settings.OPENAI_BASE_URL:
        logger.warning("No API key/base URL — skipping session evaluation.")
        return None

    # Build the evaluation prompt with full transcript + metadata
    system_prompt, llm_messages = build_evaluation_prompt(
        messages=messages,
        stage_registry=STAGE_REGISTRY,
    )

    # Use a fresh client — could use a different/stronger model
    from openai import AsyncOpenAI
    base_url = settings.OPENAI_BASE_URL or None
    effective_api_key = settings.OPENAI_API_KEY or ("ollama" if base_url else "")
    if not effective_api_key:
        logger.warning("No effective API key — skipping session evaluation.")
        return None

    # Some OpenAI-compatible servers (e.g., Ollama) may not support response_format.
    supports_response_format = not (base_url and ("11434" in base_url or "ollama" in base_url.lower()))
    client = AsyncOpenAI(api_key=effective_api_key, base_url=base_url)
    eval_model = model or settings.OPENAI_MODEL

    logger.info(f"Running post-session evaluation with {eval_model}")
    start_time = time.monotonic()

    try:
        create_kwargs = {
            "model": eval_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *llm_messages,
            ],
            "temperature": 0.3,  # Lower temp for analytical precision
            "max_tokens": 2048,  # Evaluation needs more room
        }
        if supports_response_format:
            create_kwargs["response_format"] = {"type": "json_object"}

        completion = await client.chat.completions.create(**create_kwargs)

        raw_content = completion.choices[0].message.content
        if not raw_content:
            logger.error("Empty response from evaluation LLM call.")
            return None

        evaluation = json.loads(raw_content)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        token_usage = {}
        if completion.usage:
            token_usage = {
                "prompt": completion.usage.prompt_tokens,
                "completion": completion.usage.completion_tokens,
                "total": completion.usage.total_tokens,
            }

        # Attach evaluation metadata
        evaluation["_eval_metadata"] = {
            "model": eval_model,
            "response_time_ms": elapsed_ms,
            "token_usage": token_usage,
        }

        logger.info(
            f"Session evaluation complete: {elapsed_ms}ms, "
            f"{token_usage.get('total', '?')} tokens, "
            f"score={evaluation.get('session_quality', {}).get('overall_score', '?')}/5"
        )

        return evaluation

    except json.JSONDecodeError as e:
        logger.error(f"Evaluation returned invalid JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Session evaluation failed: {e}")
        return None
