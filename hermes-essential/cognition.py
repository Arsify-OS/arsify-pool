"""
layers/cognition.py  — L2 Cognition (Planner)
────────────────────────────────────────────────────────────────────────────────
Accepts L1 perception + optional SKP context. Returns an atomic execution plan.
"""

import json
import logging

from core.knowledge_injector import fetch_relevant_context
from models.cache import cached_call as call_with_fallback

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are L2 Cognition Engine (Planner) of Hermes AI.
Version: v1.0 | Temperature: 0.3 | Layer: L2

RULES:
- Return ONLY valid JSON — no markdown, no explanation, no code fences
- Do NOT wrap response in ```json ... ```
- Output must be parseable by json.loads() directly

Task:
- Read the perception from L1 and any SKP context
- Break the goal into 2-4 atomic, executable steps
- Assign type to each step: planning | execution | devops | analysis | creative

Output schema (must match exactly):
{
  "version": "v1.0",
  "layer": "L2",
  "goal": "<restatement of the goal>",
  "steps": [
    {
      "id": <integer>,
      "task": "<atomic task description>",
      "type": "planning|execution|devops|analysis|creative",
      "tool": "<tool or 'llm'>",
      "expected_output": "<what success looks like>"
    }
  ],
  "estimated_complexity": <integer 1-10>,
  "context_used": <true|false>
}"""


async def plan_task(perception: dict, agent_profile: dict | None = None) -> dict:
    """
    L2: Generate an execution plan from L1 perception.
    Injects SKP context if available.
    """
    # Inject knowledge from SKP
    context_str  = fetch_relevant_context(perception)
    context_used = bool(context_str)

    context_block = (
        f"\nCONTEXT FROM ARCHIVIST™ (SKP):\n{context_str}\n"
        if context_str
        else "\nCONTEXT FROM ARCHIVIST™: No prior context found.\n"
    )

    prompt = (
        "You are L2 Planner. Output ONLY valid JSON — no markdown, no code fences, no explanation.\n"
        "Schema: {\"goal\":\"<goal>\",\"steps\":[{\"id\":N,\"task\":\"<task>\",\"type\":\"execution|analysis|planning|devops|creative\",\"tool\":\"<tool>\",\"expected_output\":\"<output>\"}],\"estimated_complexity\":N,\"context_used\":false}\n"
        f"PERCEPTION:\n{json.dumps(perception)}"
        f"{context_block}"
        "Output ONLY the JSON plan:"
    )

    result = await call_with_fallback("nemotron", prompt, fallback="fallback")

    if result.get("error"):
        logger.warning("L2: LLM call failed (%s) — using fallback plan", result["error"])
        return _fallback_plan(perception, context_used)

    content = result.get("content", "")
    return _parse_plan(content, perception, context_used)


def _parse_plan(content: str, perception: dict, context_used: bool) -> dict:
    text = content.strip()
    
    # Strategy 1: Remove markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                end = i
                break
        text = "\n".join(lines[start:end]).strip()
    
    # Strategy 2: Try direct JSON parse
    try:
        plan = json.loads(text)
        plan.setdefault("version", "v1.0")
        plan.setdefault("layer", "L2")
        plan.setdefault("context_used", context_used)
        plan.setdefault("steps", [])
        if plan.get("steps"):
            return plan
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Strategy 3: Extract JSON object from text using regex — try multiple patterns
    import re
    # Try to find any JSON object with "steps" array
    for pattern in [
        r'\{[^{]*"steps"\s*:\s*\[[^\]]*\]',  # Direct "steps": [...]
        r'"execution_plan"\s*:\s*\{[^}]*"steps"\s*:\s*\[[^\]]*\]',  # Nested in execution_plan
    ]:
        json_match = re.search(pattern, text, re.DOTALL)
        if json_match:
            try:
                obj = json.loads(json_match.group())
                # Handle nested structure
                if "execution_plan" in obj:
                    obj = obj["execution_plan"]
                if obj.get("steps"):
                    # Normalize step format
                    normalized_steps = []
                    for i, s in enumerate(obj["steps"]):
                        normalized_steps.append({
                            "id": s.get("step_number", s.get("id", i + 1)),
                            "task": s.get("action", s.get("task", str(s)))[:150],
                            "type": s.get("type", "execution"),
                            "tool": s.get("tool", "llm"),
                            "expected_output": s.get("expected_outcome", s.get("expected_output", ""))[:100],
                        })
                    plan = {
                        "version": "v1.0",
                        "layer": "L2",
                        "goal": obj.get("description", perception.get("intent", "Process request")),
                        "steps": normalized_steps,
                        "estimated_complexity": perception.get("complexity", 5),
                        "context_used": context_used,
                        "_json_extracted": True,
                    }
                    logger.info("L2: parsed JSON via regex extraction (%d steps)", len(normalized_steps))
                    return plan
            except (json.JSONDecodeError, TypeError):
                pass
    
    # Strategy 4: Build plan from numbered list in text
    steps = _extract_steps_from_text(text, perception)
    if steps:
        logger.info("L2: built plan from text extraction (%d steps)", len(steps))
        return {
            "version": "v1.0",
            "layer": "L2",
            "goal": perception.get("intent", "Process request"),
            "steps": steps,
            "estimated_complexity": perception.get("complexity", 5),
            "context_used": context_used,
            "_text_extracted": True,
        }
    
    return _fallback_plan(perception, context_used)


def _extract_steps_from_text(text: str, perception: dict) -> list:
    """Try to extract steps from numbered/bulleted list in LLM text response."""
    import re
    steps = []
    intent = perception.get("intent", "Process request")
    category = perception.get("category", "general")
    
    # Match numbered items: "1. **Title**\n   - task" or "1. **Title**: description"
    numbered = re.findall(r'\d+\.\s+\*\*([^*]+)\*\*[:\s]*([^\n]*)', text)
    if not numbered:
        # Try: "1. Title — description" or "1. Title"
        numbered = re.findall(r'\d+\.\s+([^-\n]+?)(?:\s*[-—:]\s*([^\n]*))?', text)
    
    for i, match in enumerate(numbered[:4]):  # Max 4 steps
        title = match[0].strip() if isinstance(match, tuple) else match.strip()
        desc = match[1].strip() if isinstance(match, tuple) and len(match) > 1 else ""
        task = f"{title}: {desc}" if desc else title
        if task and len(task) > 5:
            # Determine step type from content
            task_lower = task.lower()
            if any(w in task_lower for w in ("assess", "analyze", "research", "understand", "gather")):
                step_type = "analysis"
            elif any(w in task_lower for w in ("design", "plan", "select", "choose")):
                step_type = "planning"
            else:
                step_type = "execution"
            steps.append({
                "id": i + 1,
                "task": task[:150],
                "type": step_type,
                "tool": "llm",
                "expected_output": title[:100],
            })
    
    return steps


def _fallback_plan(perception: dict, context_used: bool) -> dict:
    """
    Fallback plan yang menghasilkan steps meaningful berdasarkan perception.
    Bukan generic 'Process request' tapi breakdown aktual dari intent.
    """
    intent = perception.get("intent", "Process request")
    category = perception.get("category", "general")
    complexity = perception.get("complexity", 5)

    # Generate meaningful steps based on category
    if category in ("backend", "devops", "infrastructure"):
        steps = [
            {"id": 1, "task": f"Analyze requirements: {intent}", "type": "analysis", "tool": "llm", "expected_output": "Structured requirements breakdown"},
            {"id": 2, "task": f"Design solution approach for: {intent}", "type": "planning", "tool": "llm", "expected_output": "Solution design document"},
            {"id": 3, "task": f"Implement and validate: {intent}", "type": "execution", "tool": "llm", "expected_output": "Working implementation with validation"},
        ]
    elif category in ("research", "academic", "analysis"):
        steps = [
            {"id": 1, "task": f"Research and gather information: {intent}", "type": "analysis", "tool": "llm", "expected_output": "Comprehensive research findings"},
            {"id": 2, "task": f"Synthesize and analyze findings for: {intent}", "type": "analysis", "tool": "llm", "expected_output": "Structured analysis with insights"},
            {"id": 3, "task": f"Draw conclusions and recommendations: {intent}", "type": "execution", "tool": "llm", "expected_output": "Actionable conclusions and recommendations"},
        ]
    elif category in ("business", "strategy", "market"):
        steps = [
            {"id": 1, "task": f"Market/context analysis: {intent}", "type": "analysis", "tool": "llm", "expected_output": "Market analysis summary"},
            {"id": 2, "task": f"Strategic assessment: {intent}", "type": "planning", "tool": "llm", "expected_output": "Strategic options and evaluation"},
            {"id": 3, "task": f"Recommendations and action plan: {intent}", "type": "execution", "tool": "llm", "expected_output": "Actionable recommendations"},
        ]
    else:
        # General — 2 steps minimum
        steps = [
            {"id": 1, "task": f"Analyze and understand: {intent}", "type": "analysis", "tool": "llm", "expected_output": "Clear understanding of the request"},
            {"id": 2, "task": f"Execute and deliver: {intent}", "type": "execution", "tool": "llm", "expected_output": "Complete and detailed response"},
        ]

    return {
        "version":              "v1.0",
        "layer":                "L2",
        "goal":                 intent,
        "steps":                steps,
        "estimated_complexity": complexity,
        "context_used":         context_used,
        "_fallback":            True,
    }
