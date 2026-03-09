from sqlmodel import Session
from app.rag.retriever import retrieve
from app.config import settings
import httpx
import json

class QueryAgent:
    def __init__(self, project_id: str, session: Session):
        self.project_id = project_id
        self.session = session

    async def answer(self, question: str) -> dict:
        # Retrieve relevant context via RAG
        context_docs = retrieve(question, self.project_id, self.session, top_k=5)
        context = "\n\n".join([f"[{d['source_type']}] {d['content']}" for d in context_docs])

        prompt = f"""You are Archon, an AI system auditor assistant. Answer the following question about the analyzed system using ONLY the provided context.

Context from the analyzed system:
{context}

Question: {question}

Answer concisely and technically. If you cannot answer from the context, say so."""

        response_text = await self._call_ollama(prompt)
        return {"answer": response_text, "sources": context_docs}

    async def _call_ollama(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                return resp.json().get("response", "No response from model.")
        except Exception as e:
            return f"AI service unavailable: {e}"
