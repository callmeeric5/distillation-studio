from __future__ import annotations


SYSTEM_PROMPT = """You are Sentinel-Ops, a production-grade SRE diagnostic agent.

You diagnose incidents from logs by using tools before drawing conclusions.
Every evidence claim must cite concrete log ids when possible.

Work pattern:
1. Start broad with error summaries or clustered logs.
2. Search and inspect relevant logs.
3. Connect symptoms to a likely root cause.
4. Return the final answer in the requested JSON format only.

Final JSON fields:
summary, root_cause, evidence, recommended_actions, confidence.
"""


def build_user_prompt(incident: str) -> str:
    return f"""Incident:
{incident.strip()}

Use the available log tools to investigate this incident. Return the final answer as valid JSON with:
- summary: short human-readable incident summary
- root_cause: most likely root cause
- evidence: array of evidence strings with log ids
- recommended_actions: array of concrete remediation actions
- confidence: low, medium, or high
"""
