"""Stage registry endpoint — exposes conversation stage config to the frontend."""

from fastapi import APIRouter

from app.core.prompts import STAGE_REGISTRY, STAGE_ORDER

router = APIRouter(prefix="/stages", tags=["stages"])


@router.get("")
def get_stages() -> dict:
    """
    Return the full stage registry and ordering.

    Used by the frontend inspector to show what criteria the LLM
    was evaluated against at each stage, without hardcoding.
    """
    return {
        "stages": STAGE_REGISTRY,
        "order": STAGE_ORDER,
    }
