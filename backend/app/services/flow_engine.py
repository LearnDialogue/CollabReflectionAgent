"""
FlowEngine - Core conversation flow management with hybrid transitions.

Orchestrates the conversation by building prompts, calling the LLM client,
interpreting structured responses, and managing stage transitions.

The FlowEngine is the SOLE AUTHORITY on stage transitions. The LLM's
stage_completed and routing_signal are treated as recommendations, not
commands. The engine applies deterministic guardrails:
  - min_turns: never advance before the minimum
  - max_turns: always advance after the maximum
  - required_signals: heuristic keyword checks on student messages
  - time limits: force wrap-up if session exceeds time budget

The conversation protocol is grounded in:
  - SRL (Winne & Hadwin, 1998): Task Definition → Goal Setting & Planning →
    Strategy Enactment → Adaptation
  - SSRL (Järvelä & Hadwin, 2013): Extends SRL to the group level
  - CPS (PISA 2015): Collaborative problem solving indicators (complementary)

Every transition decision is logged with full audit data in llm_metadata.
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from app.core.config import settings
from app.core.prompts import (
    STAGE_REGISTRY,
    STAGE_ORDER,
    build_system_prompt,
    build_cps_context,
)
from app.schemas.llm import RoutingSignal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session as DBSession
    from app.models.session import Session
    from app.models.message import Message
    from app.models.student import Student
    from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class FlowEngine:
    """
    Manages conversation flow through SRL/SSRL-mapped stages.

    Takes a session, its message history, the student, an LLM client,
    and optionally a database session (for CPS indicator lookup and
    cross-session memory with regulatory growth tracking).

    process() calls the LLM and returns the response text, new stage,
    completion flag, and metadata to persist.
    """

    def __init__(
        self,
        session: "Session",
        history: list["Message"],
        student: "Student",
        llm_client: "LLMClient",
        db: Optional["DBSession"] = None,
    ):
        self.session = session
        self.history = history
        self.student = student
        self.llm_client = llm_client
        self.db = db
        self.current_stage = session.current_stage

    async def process(self, user_input: Optional[str] = None) -> tuple[str, str, bool, Optional[dict]]:
        """
        Process user input and generate an LLM response.

        When user_input is None the engine generates an initial greeting
        with no preceding user message (tutor-initiated conversation).

        Returns:
            (response_text, new_stage, is_complete, llm_metadata)
        """
        # Build CPS context for strategy_monitoring stage
        # CPS indicators are most relevant during the monitoring/enactment
        # phase, where students describe team interactions and coordination
        cps_context = None
        if self.current_stage == "strategy_monitoring" and self.db is not None:
            cps_context = build_cps_context(self.db)

        # Load cross-session memory from previous evaluations
        cross_session_context = self._load_cross_session_context()

        # Check time limit — force jump to wrap_up if over budget
        time_info = self._check_time_limit()
        if time_info["over_limit"] and self.current_stage != "wrap_up":
            logger.info(
                f"Time limit reached ({time_info['elapsed_seconds']}s / "
                f"{settings.SESSION_TIME_LIMIT_SECONDS}s) — forcing jump to wrap_up"
            )
            self.current_stage = "wrap_up"

        # Build system prompt for current stage
        # Add time-awareness hint if approaching the limit
        time_hint = None
        if time_info["approaching_limit"] and self.current_stage != "wrap_up":
            remaining = settings.SESSION_TIME_LIMIT_SECONDS - time_info["elapsed_seconds"]
            time_hint = (
                f"\n--- TIME AWARENESS ---\n"
                f"This session has about {int(remaining / 60)} minutes remaining. "
                f"Start moving toward a natural conclusion. Don't rush, but "
                f"don't start new deep exploration either."
            )

        system_prompt = build_system_prompt(
            stage_id=self.current_stage,
            student_name=self.student.display_name or self.student.username,
            pronouns=self.student.pronouns,
            tone_pref=self.student.tone_pref,
            cps_context=cps_context,
            cross_session_context=cross_session_context,
        )

        # Append time hint after prompt assembly if applicable
        if time_hint:
            system_prompt += time_hint

        # Build message history for the LLM
        messages = self._build_message_history(user_input)

        # Use the stronger quality model for wrap_up (summary matters)
        use_quality_model = self.current_stage == "wrap_up"
        if use_quality_model and settings.LLM_QUALITY_MODEL != settings.LLM_MODEL:
            from app.services.llm_client import NavigatorClient
            quality_client = NavigatorClient(model=settings.LLM_QUALITY_MODEL)
            llm_result = await quality_client.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                stage_id=self.current_stage,
            )
        else:
            llm_result = await self.llm_client.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                stage_id=self.current_stage,
            )
        llm_response = llm_result.response

        # --- Hybrid transition logic ---
        transition_decision = self._should_advance(
            llm_response.stage_completed,
            llm_response.routing_signal,
            user_input,
        )

        # Apply the engine's decision (may override the LLM)
        if transition_decision["engine_decided"] == "NEXT":
            llm_response.stage_completed = True
            llm_response.routing_signal = RoutingSignal.NEXT
        else:
            llm_response.stage_completed = False
            llm_response.routing_signal = RoutingSignal.STAY

        # Determine new stage
        stage_config = STAGE_REGISTRY.get(self.current_stage, {})
        new_stage = self.current_stage
        if llm_response.stage_completed and llm_response.routing_signal == RoutingSignal.NEXT:
            next_stage = stage_config.get("next_stage")
            if next_stage:
                new_stage = next_stage

        # Session is complete when wrap_up stage is completed
        is_complete = (
            self.current_stage == "wrap_up" and llm_response.stage_completed
        )

        # Build metadata to save alongside the assistant message
        llm_metadata = {
            "routing_signal": llm_response.routing_signal.value,
            "stage_completed": llm_response.stage_completed,
            "tutor_gesture": llm_response.tutor_gesture.value,
            "tutor_expression": llm_response.tutor_expression.value,
            "reflection_data": llm_response.reflection_data,
            "model": settings.LLM_QUALITY_MODEL if use_quality_model else settings.LLM_MODEL,
            "prompt_version": "v2",
            "forced_advance": transition_decision.get("reason", "").startswith("max_turns"),
            "transition_decision": transition_decision,
            "time_info": time_info,
            "response_time_ms": llm_result.response_time_ms,
            "token_usage": llm_result.token_usage,
            "attempt_number": llm_result.attempt_number,
        }

        return llm_response.tutor_response, new_stage, is_complete, llm_metadata

    def _should_advance(
        self,
        llm_stage_completed: bool,
        llm_routing_signal: RoutingSignal,
        user_input: Optional[str],
    ) -> dict:
        """
        Hybrid transition decision — the FlowEngine is the sole authority.

        Decision matrix:
          1. turn_count < min_turns        → STAY (never advance too early)
          2. turn_count >= max_turns        → NEXT (force advance)
          3. LLM says STAY                  → STAY
          4. LLM says NEXT + signals met   → NEXT
          5. LLM says NEXT + signals unmet → STAY (override LLM)

        Returns a dict with full audit trail for llm_metadata.
        """
        stage_config = STAGE_REGISTRY.get(self.current_stage, {})
        min_turns = stage_config.get("min_turns", 1)
        max_turns = stage_config.get("max_turns", settings.LLM_STAGE_MAX_TURNS)
        required_signals = stage_config.get("required_signals", {})

        turn_count = self._count_stage_turns()

        # Check which required signals are met
        student_messages = self._get_stage_student_messages(user_input)
        signals_met, signals_missing = self._check_required_signals(
            required_signals, student_messages
        )

        llm_suggested = "NEXT" if (llm_stage_completed and llm_routing_signal == RoutingSignal.NEXT) else "STAY"

        # --- Decision matrix ---

        # Rule 1: Never advance before min_turns
        if turn_count < min_turns:
            return {
                "llm_suggested": llm_suggested,
                "engine_decided": "STAY",
                "reason": f"min_turns not reached ({turn_count} < {min_turns})",
                "turn_count": turn_count,
                "min_turns": min_turns,
                "max_turns": max_turns,
                "signals_met": list(signals_met),
                "signals_missing": list(signals_missing),
            }

        # Rule 2: Always advance after max_turns
        if turn_count >= max_turns:
            logger.info(
                f"Hybrid transition: force-advancing from '{self.current_stage}' "
                f"after {turn_count} turns (max: {max_turns})"
            )
            return {
                "llm_suggested": llm_suggested,
                "engine_decided": "NEXT",
                "reason": f"max_turns reached ({turn_count} >= {max_turns})",
                "turn_count": turn_count,
                "min_turns": min_turns,
                "max_turns": max_turns,
                "signals_met": list(signals_met),
                "signals_missing": list(signals_missing),
            }

        # Rule 3: If LLM says STAY, respect it
        if llm_suggested == "STAY":
            return {
                "llm_suggested": "STAY",
                "engine_decided": "STAY",
                "reason": "LLM recommended STAY",
                "turn_count": turn_count,
                "min_turns": min_turns,
                "max_turns": max_turns,
                "signals_met": list(signals_met),
                "signals_missing": list(signals_missing),
            }

        # Rule 4 & 5: LLM says NEXT — check required signals
        if signals_missing:
            logger.info(
                f"Hybrid transition: overriding LLM NEXT for '{self.current_stage}' — "
                f"missing signals: {signals_missing}"
            )
            return {
                "llm_suggested": "NEXT",
                "engine_decided": "STAY",
                "reason": f"required_signals not met: {', '.join(signals_missing)}",
                "turn_count": turn_count,
                "min_turns": min_turns,
                "max_turns": max_turns,
                "signals_met": list(signals_met),
                "signals_missing": list(signals_missing),
            }

        # All checks passed — advance
        return {
            "llm_suggested": "NEXT",
            "engine_decided": "NEXT",
            "reason": "LLM recommended NEXT, all signals met",
            "turn_count": turn_count,
            "min_turns": min_turns,
            "max_turns": max_turns,
            "signals_met": list(signals_met),
            "signals_missing": [],
        }

    def _check_required_signals(
        self,
        required_signals: set,
        student_messages: list[str],
    ) -> tuple[list[str], list[str]]:
        """
        Check whether the student's messages contain the required
        conversational elements for stage advancement.

        This is intentionally simple — keyword/pattern matching,
        NOT semantic analysis. We want deterministic, auditable logic
        that a researcher can independently verify.

        Returns:
            (signals_met, signals_missing) — two lists of signal names.
        """
        if not required_signals:
            return [], []

        combined = " ".join(student_messages).lower()
        met = []
        missing = []

        for signal in required_signals:
            if self._signal_detected(signal, combined):
                met.append(signal)
            else:
                missing.append(signal)

        return met, missing

    @staticmethod
    def _signal_detected(signal: str, combined_text: str) -> bool:
        """
        Check if a specific signal is detected in the combined student text.

        Each signal has its own set of keyword patterns. These are
        deliberately simple — not NLP or semantic analysis.
        """
        if not combined_text.strip():
            return False

        patterns: dict[str, list[str]] = {
            "described_task": [
                "today", "yesterday", "meeting", "worked on", "happened",
                "we did", "we tried", "session", "last time", "earlier",
                "this week", "practice", "after school", "we were",
                "the task", "the project", "our goal", "what we needed",
                "supposed to", "had to", "needed to", "the assignment",
            ],
            "mentioned_teammate": [
                "teammate", "team", "partner", "they ", "he ", "she ",
                "we ", "us ", "our ", "my group", "my partner",
                "everyone", "nobody", "someone", "the other",
            ],
            "described_planning": [
                "plan", "planned", "decided", "assigned", "divided",
                "split up", "organized", "set a goal", "agreed",
                "figured out", "laid out", "started with", "first we",
                "no plan", "didn't plan", "just started", "jumped in",
                "winged it", "who does what", "roles", "in charge",
            ],
            "described_monitoring": [
                "checked", "check in", "noticed", "realized",
                "adjusted", "changed", "switched", "stopped",
                "weren't working", "wasn't working", "went wrong",
                "hit a wall", "stuck", "problem", "struggled",
                "progress", "on track", "behind", "ahead",
                "brought it up", "said something", "pointed out",
                "regrouped", "pivot", "adapted", "fixed",
                "didn't notice", "kept going", "pushed through",
            ],
            "evaluated_outcome": [
                "worked", "didn't work", "was good", "was bad",
                "effective", "helped", "made it worse", "improved",
                "because", "realized", "i think", "reason", "probably",
                "maybe it's", "i guess", "that's why", "i noticed",
                "it makes sense", "i wonder if", "could be",
                "next time", "should have", "could have",
                "if we had", "looking back", "in hindsight",
            ],
            "proposed_adaptation": [
                "i'll", "i will", "next time", "going to", "plan to",
                "try to", "want to", "gonna", "next meeting",
                "i could", "i should", "i might", "let me",
                "check in", "regroup", "set a goal", "make a plan",
                "ask everyone", "divide up", "assign", "organize",
                "monitor", "stop and", "pause and", "step back",
            ],
        }

        signal_patterns = patterns.get(signal, [])
        if not signal_patterns:
            # Unknown signal — treat as satisfied (fail-open)
            return True

        return any(p in combined_text for p in signal_patterns)

    def _get_stage_student_messages(self, current_input: Optional[str] = None) -> list[str]:
        """
        Get all student messages from the current stage, including
        the current (not yet saved) input.
        """
        messages = [
            m.content for m in self.history
            if m.stage_id == self.current_stage and m.role.value == "user"
        ]
        if current_input is not None:
            messages.append(current_input)
        return messages

    def _build_message_history(self, current_input: Optional[str] = None) -> list[dict]:
        """
        Convert DB message history + current user input into the
        [{role, content}] format the LLM expects.

        When current_input is None (tutor-initiated greeting), the user
        message is omitted so the LLM speaks first.
        """
        messages = []
        for msg in self.history:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        # Add the current user message (only if not already the last message in history)
        if current_input is not None:
            if not messages or messages[-1]["role"] != "user" or messages[-1]["content"] != current_input:
                messages.append({
                    "role": "user",
                    "content": current_input,
                })

        return messages

    def _count_stage_turns(self) -> int:
        """Count how many assistant messages exist in the current stage."""
        return sum(
            1 for m in self.history
            if m.stage_id == self.current_stage and m.role.value == "assistant"
        )

    def _check_time_limit(self) -> dict:
        """
        Check how much time has elapsed in this session.

        Returns a dict with:
          - elapsed_seconds: seconds since session started
          - over_limit: True if session has exceeded the time limit
          - approaching_limit: True if past the wrap-up threshold
        """
        if not self.session.started_at:
            return {
                "elapsed_seconds": 0,
                "over_limit": False,
                "approaching_limit": False,
            }

        now = datetime.now(timezone.utc)
        started = self.session.started_at

        # Handle naive datetime from DB (assume UTC)
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)

        elapsed = (now - started).total_seconds()
        limit = settings.SESSION_TIME_LIMIT_SECONDS
        threshold = limit * settings.SESSION_WRAP_UP_THRESHOLD

        return {
            "elapsed_seconds": int(elapsed),
            "over_limit": elapsed >= limit,
            "approaching_limit": elapsed >= threshold,
        }


    def _load_cross_session_context(self) -> Optional[str]:
        """
        Load context from the student's most recent completed session.

        Queries the evaluation_data JSONB from the last completed session
        and extracts the student_profile, including regulatory growth data.
        This gives the agent awareness of the student's previous teamwork
        patterns, communication style, memory hooks, and — critically —
        their regulatory tendencies and growth areas for progressive
        scaffolding across sessions.

        Returns a formatted string for prompt injection, or None if no
        previous sessions exist or db is unavailable.
        """
        if self.db is None:
            return None

        from app.models.session import Session as ChatSession, SessionStatus

        # Find the most recent COMPLETED session for this student
        # (excluding the current session)
        prev_session = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.student_id == self.student.id,
                ChatSession.status == SessionStatus.COMPLETED,
                ChatSession.id != self.session.id,
            )
            .order_by(ChatSession.completed_at.desc())
            .first()
        )

        if not prev_session or not prev_session.evaluation_data:
            return None

        eval_data = prev_session.evaluation_data
        profile = eval_data.get("student_profile", {})

        if not profile:
            return None

        # Build the context string from the profile
        lines = [
            "--- PREVIOUS SESSION CONTEXT (for your reference only) ---",
            "The student has talked with you before. Here is what you know ",
            "from their last session:",
            "",
        ]

        if profile.get("team_context") and profile["team_context"] != "N/A":
            lines.append(f"- Team context: {profile['team_context']}")

        # Fall back to project_context for older evaluation data
        elif profile.get("project_context") and profile["project_context"] != "N/A":
            lines.append(f"- Project context: {profile['project_context']}")

        if profile.get("communication_style") and profile["communication_style"] != "N/A":
            lines.append(f"- Communication style: {profile['communication_style']}")

        if profile.get("teamwork_patterns") and profile["teamwork_patterns"] != "N/A":
            lines.append(f"- Teamwork patterns: {profile['teamwork_patterns']}")

        if profile.get("regulation_tendencies") and profile["regulation_tendencies"] != "N/A":
            lines.append(f"- Regulation tendencies: {profile['regulation_tendencies']}")

        if profile.get("emotional_patterns") and profile["emotional_patterns"] != "N/A":
            lines.append(f"- Emotional patterns: {profile['emotional_patterns']}")

        memory_hooks = profile.get("memory_hooks", [])
        if memory_hooks and memory_hooks != ["N/A"]:
            lines.append(f"- Memory hooks: {'; '.join(memory_hooks)}")

        unresolved = profile.get("unresolved_topics", [])
        if unresolved and unresolved != ["N/A"]:
            lines.append(f"- Unresolved from last time: {'; '.join(unresolved)}")

        # Regulatory growth tracking — enables progressive scaffolding
        reg_growth = profile.get("regulatory_growth", {})
        if reg_growth:
            growth_lines = []
            if reg_growth.get("current_awareness_level") and reg_growth["current_awareness_level"] != "N/A":
                growth_lines.append(
                    f"  Regulatory awareness: {reg_growth['current_awareness_level']}"
                )
            growth_areas = reg_growth.get("growth_areas", [])
            if growth_areas and growth_areas != ["N/A"]:
                growth_lines.append(
                    f"  Areas for growth: {'; '.join(growth_areas)}"
                )
            strengths = reg_growth.get("strengths", [])
            if strengths and strengths != ["N/A"]:
                growth_lines.append(
                    f"  Regulatory strengths: {'; '.join(strengths)}"
                )
            focus = reg_growth.get("recommended_focus_next_session")
            if focus and focus != "N/A":
                growth_lines.append(
                    f"  Recommended focus this session: {focus}"
                )
            if growth_lines:
                lines.append("- Regulatory growth (from last session's evaluation):")
                lines.extend(growth_lines)

        # Collaborative behavior tracking (CPS framework indicators) from previous session
        cps_analysis = eval_data.get("cps_complaint_analysis", {})
        if cps_analysis:
            cps_lines = []
            if cps_analysis.get("cps_summary") and cps_analysis["cps_summary"] != "N/A":
                cps_lines.append(f"  Summary: {cps_analysis['cps_summary']}")
            
            complaints = cps_analysis.get("complaints", [])
            if complaints:
                for c in complaints:
                    valence_str = "Breakdown" if c.get("valence") == "negative" else "Positive behavior"
                    cps_lines.append(
                        f"  - {valence_str} under facet '{c.get('facet')}' (Indicator: {c.get('indicator')}) "
                        f"described as: \"{c.get('complaint_text')}\""
                    )
            
            if cps_lines:
                lines.append("- Collaborative dynamics (CPS framework) observed last time:")
                lines.extend(cps_lines)

        # Only return if we actually have useful content (not just the header)
        if len(lines) <= 4:
            return None

        lines.append("")
        lines.append(
            "IMPORTANT: Do NOT proactively bring up these details. Only "
            "reference them if the student mentions something related first. "
            "If they say something that connects to a memory hook, "
            "unresolved topic, or regulatory growth area, you can naturally "
            "reference it. For regulatory growth, gently steer toward the "
            "recommended focus area when a natural opportunity arises — "
            "but NEVER use academic language about 'regulation' or 'SRL'."
        )

        logger.debug(
            f"Loaded cross-session context from session {prev_session.id} "
            f"for student {self.student.id}"
        )

        return "\n".join(lines)
