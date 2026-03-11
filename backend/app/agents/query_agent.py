from sqlmodel import Session
from app.rag.retriever import retrieve
from app.models.db import UserCredential
from app.services.ai_client import complete, NoCredentialError
from app.core.crypto import decrypt
from app.config import settings
import httpx
import json
from typing import AsyncIterator, Optional


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


class QueryAgent:
    def __init__(self, project_id: str, session: Session, credential: Optional[UserCredential] = None):
        self.project_id = project_id
        self.session = session
        self.credential = credential

    def _model_label(self) -> str:
        if not self.credential:
            return "no model"
        return f"{self.credential.provider}/{self.credential.model}"

    async def stream(self, question: str) -> AsyncIterator[str]:
        if not self.credential:
            yield _sse({"type": "step", "text": "Searching knowledge base..."})
            yield _sse({"type": "step", "text": "Found 0 relevant document(s)"})
            yield _sse({"type": "token", "text": "No active AI credential configured. Please go to **Credentials** and activate a model first."})
            yield _sse({"type": "done", "answer": "", "sources": []})
            return

        yield _sse({"type": "step", "text": "Searching knowledge base..."})
        context_docs = retrieve(question, self.project_id, self.session, top_k=5)
        yield _sse({"type": "context", "sources": context_docs, "count": len(context_docs)})
        yield _sse({"type": "step", "text": f"Found {len(context_docs)} relevant document(s)"})

        context = "\n\n".join([f"[{d['source_type']}] {d['content']}" for d in context_docs])
        prompt = f"""You are Archon, an AI system auditor assistant. Answer the following question about the analyzed system using ONLY the provided context.

Context from the analyzed system:
{context}

Question: {question}

Answer concisely and technically. If you cannot answer from the context, say so."""

        yield _sse({"type": "prompt", "text": prompt})
        yield _sse({"type": "step", "text": f"Sending to {self._model_label()}..."})

        full_answer = ""

        # Ollama supports token streaming natively
        if self.credential.provider == "ollama":
            base_url = self.credential.base_url or settings.OLLAMA_BASE_URL
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream(
                        "POST",
                        f"{base_url.rstrip('/')}/api/generate",
                        json={"model": self.credential.model, "prompt": prompt, "stream": True},
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                full_answer += token
                                yield _sse({"type": "token", "text": token})
                            if data.get("done"):
                                break
            except Exception as e:
                full_answer = f"AI service unavailable: {e}"
                yield _sse({"type": "token", "text": full_answer})

        else:
            # Other providers: call complete() and yield the full response
            try:
                full_answer = await complete(prompt, self.credential)
                yield _sse({"type": "token", "text": full_answer})
            except Exception as e:
                full_answer = f"AI service unavailable: {e}"
                yield _sse({"type": "token", "text": full_answer})

        yield _sse({"type": "done", "answer": full_answer, "sources": context_docs})
