"""AI review pass — runs after rule-based audit to enrich, filter and extend findings."""
import json
import logging
import re
from typing import Optional
from sqlmodel import Session
from app.models.db import AuditFinding, ApiEndpoint, DbTable, UserCredential
from app.services.ai_client import complete

logger = logging.getLogger(__name__)

SEVERITIES = {"critical", "high", "medium", "low", "info"}
CATEGORIES = {"api", "database", "security", "performance"}

DEFAULT_SYSTEM_PROMPT = (
    "You are an expert security and software auditor. "
    "Review the provided findings carefully and improve audit quality."
)


def _build_prompt(
    findings: list[AuditFinding],
    endpoints: list[ApiEndpoint],
    tables: list[DbTable],
    context: dict = {},
    session: Session | None = None,
) -> str:
    ep_summary = "\n".join(
        f"  {e.method.upper()} {e.path} (auth={e.auth_required})"
        for e in endpoints[:30]
    )
    if len(endpoints) > 30:
        ep_summary += f"\n  ... and {len(endpoints) - 30} more"

    tbl_summary = "\n".join(
        f"  {t.table_name}: {len(t.columns or [])} columns, {t.row_count or 0} rows"
        for t in tables[:20]
    )
    if len(tables) > 20:
        tbl_summary += f"\n  ... and {len(tables) - 20} more"

    findings_json = json.dumps([
        {
            "id": f.id,
            "title": f.title,
            "severity": f.severity,
            "category": f.category,
            "description": f.description,
        }
        for f in findings
    ], indent=2)

    memory_section = ""
    if context.get("audit_count", 0) > 1:
        history = context.get("health_score_history", [])
        recurring = context.get("recurring_findings", [])
        resolved = context.get("resolved_findings", [])
        memory_section = f"""
PROJECT MEMORY (accumulated across {context['audit_count']} audits):
- Health score trend: {" → ".join(str(s) for s in history)}
- Risk level: {context.get("current_risk", "UNKNOWN")}
- Recurring issues (appeared in multiple audits): {", ".join(recurring[:5]) if recurring else "none"}
- Recently resolved issues: {", ".join(resolved[:5]) if resolved else "none"}

"""

    # Inject similar patterns seen in other projects (global knowledge)
    global_section = ""
    if session is not None:
        try:
            from app.rag.global_retriever import retrieve_global
            all_titles = " ".join(f.title for f in findings[:10])
            similar = retrieve_global(all_titles, session, top_k=5, min_similarity=0.65)
            if similar:
                lines = "\n".join(
                    f"  - [{e['severity'].upper()}] {e['title']} "
                    f"(seen {e['usage_count']}x across projects"
                    f"{', confirmed fix' if e['confirmed'] else ''}): {e['solution'][:120]}"
                    for e in similar
                )
                global_section = f"""
GLOBAL KNOWLEDGE (similar patterns seen in other projects):
{lines}

"""
        except Exception:
            pass

    return f"""Review these rule-based findings for a software system and improve the audit quality.
{memory_section}{global_section}
SYSTEM CONTEXT:
API Endpoints ({len(endpoints)} total):
{ep_summary or "  (none)"}

Database Tables ({len(tables)} total):
{tbl_summary or "  (none)"}

RULE-BASED FINDINGS:
{findings_json}

YOUR TASKS:
1. Review each finding — dismiss false positives (e.g. a missing index on a 5-row table is not critical)
2. Adjust severity if context justifies it (e.g. an unprotected /admin endpoint is more critical than /health)
3. Add new findings the rules could not detect (e.g. naming patterns suggesting insecure design, missing rate limiting on auth endpoints, etc.)
4. If recurring issues exist in the memory above, flag them as higher priority since they persist across audits

Respond with ONLY valid JSON, no explanation, no markdown:
{{
  "reviewed": [
    {{"id": "<finding_id>", "action": "keep|dismiss|adjust", "new_severity": "<severity_if_adjust>", "reason": "<one sentence>"}}
  ],
  "new_findings": [
    {{"title": "...", "severity": "critical|high|medium|low|info", "category": "api|database|security|performance", "description": "...", "recommendation": "..."}}
  ]
}}"""


async def ai_review(
    project_id: str,
    findings: list[AuditFinding],
    endpoints: list[ApiEndpoint],
    tables: list[DbTable],
    session: Session,
    credential: Optional[UserCredential] = None,
    context: dict = {},
    system_prompt: Optional[str] = None,
) -> list[AuditFinding]:
    if credential is None:
        logger.info("No active credential — skipping AI review")
        return findings

    if not findings and not endpoints and not tables:
        return findings

    prompt = _build_prompt(findings, endpoints, tables, context, session)
    resolved_system = system_prompt or DEFAULT_SYSTEM_PROMPT

    logger.info(f"Sending {len(findings)} findings to AI for review...")
    try:
        raw = await complete(prompt, credential, system=resolved_system)
        logger.info("AI response received, parsing...")
    except Exception as e:
        logger.warning(f"AI review failed, keeping rule findings as-is: {e}")
        return findings

    # Extract JSON from response (handle cases where model wraps it in markdown)
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        logger.warning("AI review: could not parse JSON response")
        return findings

    try:
        result = json.loads(match.group())
    except json.JSONDecodeError as e:
        logger.warning(f"AI review: invalid JSON — {e}")
        return findings

    findings_by_id = {f.id: f for f in findings}
    final: list[AuditFinding] = []

    # Process reviewed findings
    for review in result.get("reviewed", []):
        fid = review.get("id")
        action = review.get("action", "keep")
        finding = findings_by_id.get(fid)
        if not finding:
            continue

        if action == "dismiss":
            session.delete(finding)
            logger.info(f"AI dismissed finding: {finding.title} — {review.get('reason')}")
            continue

        if action == "adjust":
            new_sev = review.get("new_severity", "").lower()
            if new_sev in SEVERITIES:
                finding.severity = new_sev
                session.add(finding)

        final.append(finding)

    # Keep any findings not mentioned by the AI
    reviewed_ids = {r.get("id") for r in result.get("reviewed", [])}
    for f in findings:
        if f.id not in reviewed_ids:
            final.append(f)

    # Add new AI-detected findings
    for nf in result.get("new_findings", []):
        title = nf.get("title", "").strip()
        severity = nf.get("severity", "medium").lower()
        category = nf.get("category", "security").lower()
        description = nf.get("description", "").strip()
        recommendation = nf.get("recommendation", "").strip()

        if not title or severity not in SEVERITIES or category not in CATEGORIES:
            continue

        new_finding = AuditFinding(
            project_id=project_id,
            severity=severity,
            category=category,
            title=title,
            description=description,
            recommendation=recommendation,
            source="ai",
        )
        session.add(new_finding)
        final.append(new_finding)
        logger.info(f"AI added finding: {title} [{severity}]")

    session.commit()
    return final
