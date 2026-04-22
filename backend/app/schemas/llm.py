"""
LLM Response Schema — the contract between the LLM and the FlowEngine.

Every LLM call must return JSON that validates against LLMTurnResponse.
The FlowEngine never sees raw LLM text; it only sees this structured object.
"""

from enum import Enum as PyEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TutorGesture(str, PyEnum):
    """
    Avatar gesture the tutor should display while delivering a response.

    These map directly to animation clips in the Unity avatar
    (Assets/Resources/Gestures). ChatLLM.cs passes the string
    directly to animator.Play().
    """
    CELEBRATE = "celebrate"
    CONCERNED = "concerned"
    IDLE = "idle"
    KEEP_GOING = "keepGoing"
    LEAN_IN = "leanInHandOut"
    SCRATCH_HEAD = "scratchHead"
    SINGLE_WAVE = "singleWave"
    THINKING = "thinking"


class TutorExpression(str, PyEnum):
    """
    Avatar facial expression played on the expressions animator layer.

    These are separate from gestures — a gesture controls the body,
    an expression controls the face. They play simultaneously on
    different animator layers via ChatLLM.cs PlayExpression().
    """
    NEUTRAL = "neutral"
    VERY_EXCITED = "veryExcited"
    WARM_SMILE = "warmSmile"
    CONCERNED = "concerned"
    CONTEMPLATIVE = "contemplative"
    DEEP_THOUGHT = "deepThought"
    NOD = "nod"


class RoutingSignal(str, PyEnum):
    """
    Determines how the FlowEngine should handle stage transitions.
    
    Current options:
        NEXT — Student has satisfied the stage goal; advance to next stage.
        STAY — Student is still working through this stage; remain here.
    
    Future options (add here when needed):
        PREVIOUS — Student needs to revisit an earlier stage.
        JUMP_TO  — Non-linear jump (would carry a target stage_id).
    """
    NEXT = "NEXT"
    STAY = "STAY"


class LLMTurnResponse(BaseModel):
    """
    The exact JSON structure the LLM must return on every turn.
    
    This is validated by Pydantic after every LLM call.
    If validation fails, the LLM client retries or falls back to a template.
    
    Fields:
        tutor_response:    The conversational response shown to the student.
        stage_completed: Has the student satisfied the current stage's goal?
        routing_signal:  NEXT (advance) or STAY (remain in stage).
        reflection_data: Optional research extraction (never shown to user).
                         Examples: {"emotional_tone": "frustrated", 
                                    "conflict_detected": false,
                                    "engagement_level": "high"}
    """
    tutor_response: str = Field(
        ...,
        description="The conversational response to show the student.",
        min_length=1,
    )
    stage_completed: bool = Field(
        ...,
        description="True if the student has satisfied this stage's goal.",
    )
    routing_signal: RoutingSignal = Field(
        ...,
        description="NEXT to advance stage, STAY to remain.",
    )
    tutor_gesture: TutorGesture = Field(
        default=TutorGesture.IDLE,
        description=(
            "Avatar gesture to play while delivering this response. "
            "Defaults to idle if omitted or unrecognized."
        ),
    )

    @field_validator("tutor_gesture", mode="before")
    @classmethod
    def coerce_gesture(cls, v: object) -> str:
        """Accept unknown gesture strings gracefully — fall back to idle."""
        if v is None:
            return TutorGesture.IDLE
        if isinstance(v, str):
            try:
                return TutorGesture(v)
            except ValueError:
                return TutorGesture.IDLE
        return v

    tutor_expression: TutorExpression = Field(
        default=TutorExpression.NEUTRAL,
        description=(
            "Avatar facial expression to play alongside the gesture. "
            "Defaults to neutral if omitted or unrecognized."
        ),
    )

    @field_validator("tutor_expression", mode="before")
    @classmethod
    def coerce_expression(cls, v: object) -> str:
        """Accept unknown expression strings gracefully — fall back to neutral."""
        if v is None:
            return TutorExpression.NEUTRAL
        if isinstance(v, str):
            try:
                return TutorExpression(v)
            except ValueError:
                return TutorExpression.NEUTRAL
        return v

    reflection_data: Optional[dict] = Field(
        default=None,
        description=(
            "Researcher-facing metadata. Never shown to the student. "
            "Expected keys: routing_reason (why NEXT/STAY), criteria_met "
            "(which criteria satisfied or missing), emotional_tone, "
            "engagement_level, notable_signals."
        ),
    )
