"""
Session Evaluator — post-session analysis via a single LLM call.

When a session completes, this service compiles the full conversation
transcript with all per-turn metadata, sends it to the LLM with a
strict evaluation prompt, and returns structured JSON analysis.

The evaluation assesses the session through the lens of:
  - SRL (Winne & Hadwin, 1998): Quality of each regulatory phase
  - SSRL (Järvelä & Hadwin, 2013): Shared vs. individual regulation
  - CPS (PISA 2015): Collaborative problem solving indicators
  - Regulatory growth: Cross-session tracking of metacognitive development

This is a separate call from the per-turn conversation. It runs once
per completed session and uses the full context window.
"""

import json
import logging
import time
from typing import Optional

# pyrefly: ignore [missing-import]
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.prompts import STAGE_REGISTRY, build_evaluation_prompt

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
        model:    Override model name. Defaults to the configured model.

    Returns:
        Parsed evaluation JSON dict, or None if the call fails.
    """
    if not settings.LLM_API_KEY:
        logger.warning("No LLM API key — skipping session evaluation.")
        return None

    client = AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )
    eval_model = model or settings.LLM_MODEL

    # Build the evaluation prompt with full transcript + metadata
    system_prompt, llm_messages = build_evaluation_prompt(
        messages=messages,
        stage_registry=STAGE_REGISTRY,
    )

    logger.info(f"Running post-session evaluation with {eval_model}")
    start_time = time.monotonic()

    try:
        # Try with JSON mode first, fall back to plain if unsupported
        try:
            completion = await client.chat.completions.create(
                model=eval_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *llm_messages,
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2048,
            )
        except Exception:
            completion = await client.chat.completions.create(
                model=eval_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *llm_messages,
                ],
                temperature=0.3,
                max_tokens=2048,
            )

        raw_content = completion.choices[0].message.content
        if not raw_content:
            logger.error("Empty response from evaluation LLM call.")
            return None

        # Strip markdown fences if the model wraps JSON in ```
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        evaluation = json.loads(cleaned)

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
