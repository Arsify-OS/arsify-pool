"""
layers/execution.py  — L3 Execution
────────────────────────────────────────────────────────────────────────────────
Executes a single step from the L2 plan using the appropriate model.
Model selection is driven by the step's `type` field — eliminating the
fragile string-matching (`"deploy" in task.lower()`) from the original.
"""

import json
import logging

from models.cache import cached_call as call_with_fallback

logger = logging.getLogger(__name__)

# ── Model routing table ────────────────────────────────────────────────────────
# Keyed on step.type from L2. Explicit mapping — no string matching heuristics.

TYPE_TO_MODEL: dict[str, str] = {
    "devops":    "hy3",
    "execution": "minimax",
    "planning":  "nemotron",
    "analysis":  "nemotron",
    "creative":  "minimax",
}
DEFAULT_MODEL  = "minimax"
FALLBACK_MODEL = "fallback"

_SYSTEM_PROMPT = """You are L3 Execution Engine of Hermes AI.
Version: v1.0 | Temperature: 0.2 | Layer: L3

Task:
- Execute the assigned step precisely and thoroughly
- Produce a detailed, substantive output — NOT a summary or placeholder
- If the step asks for analysis, provide actual analysis with data/insights
- If the step asks for research, provide actual findings
- If the step asks for recommendations, provide specific actionable items

Rules:
- Return JSON ONLY
- No explanation, no markdown
- The "result" field must contain the FULL output, not a summary
- Minimum 200 characters for the result field
- Be specific, detailed, and actionable

Output schema (strict):
{
  "version": "v1.0",
  "layer": "L3",
  "step_id": <integer>,
  "status": "success|failed|partial",
  "result": "<detailed output or artifact — minimum 200 chars>",
  "error": null or "<error description>",
  "model_used": "<model name>"
}"""


async def execute_step(step: dict, agent_model_override: str | None = None) -> dict:
    """
    L3: Execute a single step from the L2 plan.

    Model is chosen from TYPE_TO_MODEL based on step.type.
    Falls back to DEFAULT_MODEL if type is unrecognized.
    """
    step_type  = step.get("type", "execution")
    step_id    = step.get("id", 0)
    model_name = TYPE_TO_MODEL.get(step_type, DEFAULT_MODEL)

    logger.info("L3: executing step_id=%d type=%s model=%s", step_id, step_type, model_name)

    prompt = (
        "You are L3 Executor. Output ONLY valid JSON — no markdown, no code fences.\n"
        "Schema: {\"version\":\"v1.0\",\"layer\":\"L3\",\"step_id\":N,\"status\":\"success\",\"result\":\"<detailed output min 200 chars>\",\"error\":null,\"model_used\":\"qwen2.5:1.5b\"}\n"
        f"Step to execute: {json.dumps(step)}"
        "\nOutput ONLY the JSON result:"
    )

    result = await call_with_fallback(model_name, prompt, fallback=FALLBACK_MODEL)

    if result.get("error"):
        logger.warning("L3: step_id=%d failed: %s", step_id, result["error"])
        return {
            "version":   "v1.0",
            "layer":     "L3",
            "step_id":   step_id,
            "status":    "failed",
            "result":    None,
            "error":     result["error"],
            "model_used": model_name,
        }

    content = result.get("content", "")
    return _parse_execution(content, step_id, model_name)


def _parse_execution(content: str, step_id: int, model_name: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1 if lines[0].startswith("```") else 0
        end   = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text  = "\n".join(lines[start:end]).strip()

    try:
        parsed = json.loads(text)
        parsed.setdefault("version", "v1.0")
        parsed.setdefault("layer", "L3")
        parsed.setdefault("step_id", step_id)
        parsed.setdefault("model_used", model_name)
        return parsed
    except (json.JSONDecodeError, TypeError):
        # Non-JSON output — treat as a successful result with raw string
        return {
            "version":   "v1.0",
            "layer":     "L3",
            "step_id":   step_id,
            "status":    "success",
            "result":    content[:2000],
            "error":     None,
            "model_used": model_name,
        }
