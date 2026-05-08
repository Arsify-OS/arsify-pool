"""
layers/reflection.py  — L4 Reflection
────────────────────────────────────────────────────────────────────────────────
BUG FIX: original had no explicit criteria for when needs_replan=true.
This version provides explicit rules in the prompt AND enforces a max replan
count to prevent infinite loops.
"""

import json
import logging

from models.openrouter_client import call_with_fallback

logger = logging.getLogger(__name__)

MAX_REPLANS = int(__import__("os").getenv("HERMES_MAX_REPLANS", "2"))

_SYSTEM_PROMPT = """You are L4 Evaluator. Output ONLY valid JSON — no markdown, no code fences.

Schema: {"version":"v1.0","layer":"L4","status":"valid|invalid","quality_score":<0-100>,"issue":"<issue or null>","needs_replan":<true|false>,"replan_reason":"<reason or null>","suggested_fix":"<fix or null>"}

Rules:
- needs_replan=true ONLY if: status=failed, result=null/empty, error!=null, result contains "TODO"/"NOT IMPLEMENTED"
- quality_score: 0-100 based on completeness and accuracy
- Be critical but fair
- Output ONLY the JSON"""


async def reflect(execution_result: dict, replan_count: int = 0) -> dict:
    """
    L4: Evaluate an L3 execution result.

    Args:
        execution_result: dict from L3 execute_step()
        replan_count:     how many times we've already replanned this task

    Returns:
        reflection dict. needs_replan is forced to False if replan_count >= MAX_REPLANS.
    """
    # Auto-fail fast if execution already errored
    if execution_result.get("error") and execution_result.get("status") == "failed":
        logger.info("L4: auto-flagging for replan due to L3 error: %s", execution_result["error"])
        replan = replan_count < MAX_REPLANS
        return {
            "version":       "v1.0",
            "layer":         "L4",
            "status":        "invalid",
            "quality_score": 0,
            "issue":         f"L3 execution failed: {execution_result['error']}",
            "needs_replan":  replan,
            "replan_reason": execution_result["error"],
            "suggested_fix": "Retry with fallback model or simplify the step",
            "_auto":         True,
        }

    prompt = (
        f"{_SYSTEM_PROMPT}\n"
        f"Evaluate this execution result:\n{json.dumps(execution_result)}"
        "\nOutput ONLY the JSON evaluation:"
    )

    result = await call_with_fallback("nemotron", prompt, fallback="fallback")

    if result.get("error"):
        logger.warning("L4: LLM call failed (%s) — marking as valid to prevent loop", result["error"])
        return _safe_valid_reflection()

    content    = result.get("content", "")
    reflection = _parse_reflection(content)

    # Hard cap on replan loops
    if reflection.get("needs_replan") and replan_count >= MAX_REPLANS:
        logger.warning("L4: max replans (%d) reached — forcing needs_replan=False", MAX_REPLANS)
        reflection["needs_replan"]  = False
        reflection["replan_reason"] = None
        reflection["issue"]         = (
            f"{reflection.get('issue', '')} [replan capped at {MAX_REPLANS}]"
        )

    return reflection


def _parse_reflection(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1 if lines[0].startswith("```") else 0
        end   = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text  = "\n".join(lines[start:end]).strip()

    try:
        parsed = json.loads(text)
        parsed.setdefault("version", "v1.0")
        parsed.setdefault("layer", "L4")
        parsed.setdefault("needs_replan", False)
        parsed.setdefault("quality_score", 80)
        return parsed
    except (json.JSONDecodeError, TypeError):
        return _safe_valid_reflection()


def _safe_valid_reflection() -> dict:
    """Used when L4 itself fails — don't block the pipeline."""
    return {
        "version":       "v1.0",
        "layer":         "L4",
        "status":        "valid",
        "quality_score": 70,
        "issue":         None,
        "needs_replan":  False,
        "replan_reason": None,
        "suggested_fix": None,
        "_fallback":     True,
    }
