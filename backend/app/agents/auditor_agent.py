from sqlmodel import Session, select
from app.models.db import AuditFinding, UserCredential
from typing import Optional


class AuditorAgent:
    def __init__(self, project_id: str, session: Session, credential: Optional[UserCredential] = None):
        self.project_id = project_id
        self.session = session
        self.credential = credential

    async def prioritize_findings(self) -> dict:
        findings = self.session.exec(
            select(AuditFinding).where(AuditFinding.project_id == self.project_id)
        ).all()

        if not findings:
            return {"prioritized": [], "summary": "No findings to analyze."}

        findings_text = "\n".join([
            f"- [{f.severity.upper()}] {f.title}: {f.description}"
            for f in findings
        ])

        prompt = f"""You are Archon, an AI security and architecture auditor.

Analyze these audit findings and provide a prioritized action plan:

{findings_text}

Provide:
1. Top 3 most critical issues to fix immediately
2. A brief executive summary (2-3 sentences)
3. Overall risk assessment (Critical/High/Medium/Low)

Be concise and technical."""

        summary = await self._call_ai(prompt)

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 5))

        return {
            "prioritized": [{"id": f.id, "severity": f.severity, "title": f.title} for f in sorted_findings],
            "summary": summary,
        }

    async def _call_ai(self, prompt: str) -> str:
        try:
            from app.services.ai_client import complete, NoCredentialError
            return await complete(prompt, self.credential)
        except Exception as e:
            return f"AI analysis unavailable: {e}"
