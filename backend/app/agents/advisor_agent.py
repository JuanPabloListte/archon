from sqlmodel import Session, select
from app.models.db import AuditFinding
from app.config import settings
import httpx

class AdvisorAgent:
    def __init__(self, project_id: str, session: Session):
        self.project_id = project_id
        self.session = session

    async def get_recommendations(self, finding_id: str) -> dict:
        finding = self.session.exec(
            select(AuditFinding).where(AuditFinding.id == finding_id)
        ).first()

        if not finding:
            return {"recommendations": "Finding not found."}

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

        advice = await self._call_ollama(prompt)
        return {"finding_id": finding_id, "recommendations": advice}

    async def _call_ollama(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                return resp.json().get("response", "")
        except Exception as e:
            return f"AI advice unavailable: {e}"
