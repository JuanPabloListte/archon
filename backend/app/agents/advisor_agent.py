from sqlmodel import Session, select
from app.models.db import AuditFinding, UserCredential
from typing import Optional


class AdvisorAgent:
    def __init__(self, project_id: str, session: Session, credential: Optional[UserCredential] = None):
        self.project_id = project_id
        self.session = session
        self.credential = credential

    async def get_recommendations(self, finding_id: str) -> dict:
        finding = self.session.exec(
            select(AuditFinding).where(AuditFinding.id == finding_id)
        ).first()

        if not finding:
            return {"finding_id": finding_id, "recommendations": "Finding not found."}

        prompt = f"""You are Archon, an expert software architect and security engineer.

A system audit found the following issue:
Title: {finding.title}
Severity: {finding.severity}
Category: {finding.category}
Description: {finding.description}
Initial recommendation: {finding.recommendation}

Provide detailed, actionable technical recommendations including:
1. Step-by-step fix instructions
2. Code example if applicable
3. Best practices to prevent this issue
4. Estimated effort (hours/days)

Be specific and practical."""

        advice = await self._call_ai(prompt)
        return {"finding_id": finding_id, "recommendations": advice}

    async def _call_ai(self, prompt: str) -> str:
        try:
            from app.services.ai_client import complete
            return await complete(prompt, self.credential)
        except Exception as e:
            return f"AI advice unavailable: {e}"
