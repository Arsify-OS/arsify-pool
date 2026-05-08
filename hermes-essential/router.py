"""
core/router.py
────────────────────────────────────────────────────────────────────────────────
Unified Hermes orchestration loop — agent-aware, SKP write-back enabled.

Pipeline:
  L1 Perception → L2 Cognition (+ SKP inject) → L3+L4 loop → SKP write-back

Perubahan dari Draft Material:
  - Agent profile dipakai untuk override model priority di L3
  - L4 quality_score ≥ threshold → write entry ke SKP (learning loop)
  - agent_id diteruskan ke semua layer untuk tracking dan write-back
"""

import logging
import time
import uuid

from core.agent_registry   import get_profile, should_use_cognitive_path
from core.knowledge_injector import write_knowledge_entry
from layers.cognition  import plan_task
from layers.execution  import execute_step
from layers.perception import process_input
from layers.reflection import reflect

logger = logging.getLogger(__name__)

# Minimum L4 quality score untuk trigger write-back ke SKP
WRITE_BACK_QUALITY_THRESHOLD = 60


async def hermes_loop(
    user_input: str,
    request_id: str | None = None,
    agent_id:   str        = "default",
) -> dict:
    """
    Full Hermes cognitive pipeline dengan agent-aware routing dan SKP write-back.

    Args:
        user_input:  raw text dari user atau Hermes Agent
        request_id:  trace ID (generated jika tidak ada)
        agent_id:    X-Agent-ID dari header request (menentukan model priority)

    Returns pipeline result dict lengkap.
    """
    rid     = request_id or str(uuid.uuid4())
    start   = time.monotonic()
    profile = get_profile(agent_id)

    logger.info(
        "[%s] hermes_loop: start agent=%s input_len=%d profile=%s",
        rid, agent_id, len(user_input), profile.get("description", "")
    )

    # ── L1: Perception ───────────────────────────────────────────────────────
    perception = await process_input(user_input)
    logger.info(
        "[%s] L1: category=%s complexity=%s risk=%s",
        rid,
        perception.get("category"),
        perception.get("complexity"),
        perception.get("risk_level"),
    )

    # ── Route decision: fast vs cognitive ────────────────────────────────────
    complexity = perception.get("complexity", 5)
    if not should_use_cognitive_path(agent_id, complexity):
        # Fast path — kembalikan L1 result saja untuk Arsify OS /chat
        logger.info("[%s] → fast path (complexity=%d < threshold)", rid, complexity)
        return {
            "request_id":  rid,
            "agent_id":    agent_id,
            "route":       "fast",
            "perception":  perception,
            "plan":        None,
            "results":     [],
            "duration_ms": int((time.monotonic() - start) * 1000),
            "replans":     0,
        }

    # ── L2: Planning + SKP inject ─────────────────────────────────────────────
    # Teruskan agent profile ke L2 agar context injection relevan per agent
    plan    = await plan_task(perception, agent_profile=profile)
    steps   = plan.get("steps", [])
    replans = 0
    logger.info("[%s] L2: %d steps context_used=%s", rid, len(steps), plan.get("context_used"))

    # ── L3+L4: Execute & Reflect ──────────────────────────────────────────────
    results: list[dict] = []

    for step in steps:
        # L3: gunakan model_priority dari agent profile jika step tidak ada tipe spesifik
        execution  = await execute_step(step, agent_model_override=profile.get("model_priority"))
        reflection = await reflect(execution, replan_count=replans)

        results.append({
            "step":       step,
            "execution":  execution,
            "reflection": reflection,
        })

        quality = reflection.get("quality_score", 0)
        logger.info(
            "[%s] step=%d status=%s quality=%d needs_replan=%s",
            rid,
            step.get("id"),
            execution.get("status"),
            quality,
            reflection.get("needs_replan"),
        )

        # ── SKP Write-back: "We Own Knowledge" ──────────────────────────────
        # Setiap hasil yang berkualitas baik → masuk ke knowledge pool Upshalter
        if quality >= WRITE_BACK_QUALITY_THRESHOLD and execution.get("result"):
            _write_to_skp(
                step       = step,
                execution  = execution,
                category   = perception.get("category", "general"),
                agent_id   = agent_id,
                quality    = quality,
            )

        # ── Replan jika L4 minta ─────────────────────────────────────────────
        if reflection.get("needs_replan"):
            replans += 1
            logger.info("[%s] replan #%d: %s", rid, replans, reflection.get("replan_reason"))
            plan  = await plan_task(reflection, agent_profile=profile)
            steps = plan.get("steps", [])
            break

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info("[%s] done: %dms replans=%d agent=%s", rid, duration_ms, replans, agent_id)

    return {
        "request_id":  rid,
        "agent_id":    agent_id,
        "route":       "cognitive",
        "perception":  perception,
        "plan":        plan,
        "results":     results,
        "duration_ms": duration_ms,
        "replans":     replans,
    }


def _write_to_skp(
    step:      dict,
    execution: dict,
    category:  str,
    agent_id:  str,
    quality:   int,
):
    """
    Tulis hasil eksekusi yang berkualitas ke SKP.
    Key format: {agent_id}/{step_type}/{step_task_hash}
    Value berisi full result — Bukan summary.
    """
    task_str = step.get("task", "")
    result_str = str(execution.get("result", ""))

    key = f"{agent_id}/{step.get('type', 'exec')}/{hash(task_str) % 100000:05d}"

    # Format value yang meaningful — full result, bukan summary
    value_lines = [
        f"Step: {task_str}",
        f"Type: {step.get('type', 'execution')}",
        f"Expected: {step.get('expected_output', 'N/A')}",
        f"Quality: {quality}/100",
        f"",
        f"--- RESULT ---",
        f"{result_str}",
        f"",
        f"--- META ---",
        f"Model: {execution.get('model_used', 'unknown')}",
        f"Status: {execution.get('status', 'unknown')}",
    ]
    value = "\n".join(value_lines)[:4000]  # Increased from ~500 to 4000

    write_knowledge_entry(
        key=key,
        value=value,
        category=category,
        agent_id=agent_id,
        quality=quality,
        source="hermes_cognitive_v0.1",
    )
