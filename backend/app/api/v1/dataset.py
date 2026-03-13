"""Fine-tuning dataset export — generates training data from accumulated audit findings."""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.database import get_session
from app.models.db import User, AuditFinding, GlobalKnowledge, ApiEndpoint, DbTable, Project
from app.api.deps import get_current_user

router = APIRouter()

DEFAULT_SYSTEM_PROMPT = (
    "You are Archon, an expert software security and architecture auditor. "
    "Analyze the given system component and identify security, performance, or design issues. "
    "Be precise, technical, and actionable."
)

SYSTEM_PROMPT_PRESETS: dict[str, str] = {
    "archon": DEFAULT_SYSTEM_PROMPT,
    "security": (
        "You are a cybersecurity expert specializing in application security. "
        "Identify vulnerabilities, assess their risk, and provide remediation steps following OWASP guidelines."
    ),
    "performance": (
        "You are a software performance engineer. "
        "Analyze the given component for bottlenecks, inefficiencies, and scalability issues. "
        "Provide actionable optimizations with expected impact."
    ),
    "compliance": (
        "You are a compliance and governance auditor. "
        "Evaluate findings against industry standards (SOC2, ISO 27001, GDPR) and provide remediation guidance."
    ),
}


def _finding_to_example(finding: AuditFinding, project_name: str = "", system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> dict | None:
    """Convert a finding into a training example."""
    if not finding.title or not finding.description or not finding.recommendation:
        return None

    user_msg = (
        f"Audit finding detected in project '{project_name}':\n"
        f"Category: {finding.category}\n"
        f"Title: {finding.title}\n"
        f"Description: {finding.description}"
    )
    assistant_msg = (
        f"**Severity: {finding.severity.upper()}**\n"
        f"**Category: {finding.category}**\n\n"
        f"{finding.description}\n\n"
        f"**Recommendation:**\n{finding.recommendation}"
    )
    return {
        "messages": [
            {"role": "system",    "content": system_prompt},
            {"role": "user",      "content": user_msg},
            {"role": "assistant", "content": assistant_msg},
        ]
    }


def _global_to_example(entry: GlobalKnowledge, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> dict | None:
    """Convert a global knowledge entry to a training example."""
    if not entry.title or not entry.solution:
        return None

    confirmed_note = " This solution has been confirmed by users who resolved the issue." if entry.confirmed else ""
    user_msg = (
        f"I found this issue during an audit:\n"
        f"Title: {entry.title}\n"
        f"Description: {entry.description}"
    )
    assistant_msg = (
        f"**Severity: {entry.severity.upper()}**\n"
        f"**Category: {entry.category}**\n\n"
        f"{entry.description}\n\n"
        f"**Recommendation:**\n{entry.solution}"
        f"{confirmed_note}"
    )
    return {
        "messages": [
            {"role": "system",    "content": system_prompt},
            {"role": "user",      "content": user_msg},
            {"role": "assistant", "content": assistant_msg},
        ]
    }


@router.get("/presets")
def list_presets(current_user: User = Depends(get_current_user)):
    """Return available system prompt presets."""
    return [{"id": k, "preview": v[:120] + "..."} for k, v in SYSTEM_PROMPT_PRESETS.items()]


@router.get("/export")
def export_dataset(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    fmt: str = "jsonl",            # jsonl | alpaca
    preset: str | None = None,     # key from SYSTEM_PROMPT_PRESETS
    system_prompt: str | None = None,  # custom free-text (takes priority over preset)
):
    """
    Export fine-tuning dataset from all audit findings + global knowledge.
    - fmt=jsonl     → OpenAI/Anthropic chat format (JSONL)
    - fmt=alpaca    → Alpaca format for Ollama/Llama fine-tuning
    - preset        → use a named system prompt preset (archon, security, performance, compliance)
    - system_prompt → custom system prompt (overrides preset)
    """
    resolved_system = (
        system_prompt
        or SYSTEM_PROMPT_PRESETS.get(preset or "", DEFAULT_SYSTEM_PROMPT)
    )

    examples = []

    # From this user's project findings
    user_projects = session.exec(select(Project).where(Project.owner_id == current_user.id)).all()

    for project in user_projects:
        findings = session.exec(
            select(AuditFinding).where(AuditFinding.project_id == project.id)
        ).all()
        for f in findings:
            ex = _finding_to_example(f, project.name, resolved_system)
            if ex:
                examples.append(ex)

    # From global knowledge base (cross-project patterns)
    global_entries = session.exec(select(GlobalKnowledge)).all()
    seen_titles = {e["messages"][1]["content"][:50] for e in examples}
    for entry in global_entries:
        ex = _global_to_example(entry, resolved_system)
        if ex and ex["messages"][1]["content"][:50] not in seen_titles:
            examples.append(ex)
            seen_titles.add(ex["messages"][1]["content"][:50])

    if fmt == "alpaca":
        def _to_alpaca(ex: dict) -> dict:
            msgs = ex["messages"]
            user = next(m["content"] for m in msgs if m["role"] == "user")
            asst = next(m["content"] for m in msgs if m["role"] == "assistant")
            return {"instruction": msgs[0]["content"], "input": user, "output": asst}

        alpaca_data = [_to_alpaca(e) for e in examples]

        def generate_alpaca():
            yield json.dumps(alpaca_data, indent=2)

        return StreamingResponse(
            generate_alpaca(),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=archon_dataset.json"},
        )

    # Default: JSONL (OpenAI / Anthropic format)
    def generate_jsonl():
        for ex in examples:
            yield json.dumps(ex, ensure_ascii=False) + "\n"

    return StreamingResponse(
        generate_jsonl(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=archon_dataset.jsonl"},
    )


@router.get("/stats")
def dataset_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return dataset size statistics."""
    user_projects = session.exec(select(Project).where(Project.owner_id == current_user.id)).all()
    project_ids = [p.id for p in user_projects]

    finding_count = 0
    for pid in project_ids:
        finding_count += len(session.exec(select(AuditFinding).where(AuditFinding.project_id == pid)).all())

    global_count = len(session.exec(select(GlobalKnowledge)).all())
    confirmed_count = len([e for e in session.exec(select(GlobalKnowledge)).all() if e.confirmed])

    return {
        "your_findings": finding_count,
        "global_patterns": global_count,
        "confirmed_solutions": confirmed_count,
        "total_examples": finding_count + global_count,
    }
