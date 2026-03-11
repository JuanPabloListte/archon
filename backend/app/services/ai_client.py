"""Unified AI client — works with any configured provider or falls back to Ollama."""
import httpx
from typing import Optional
from app.models.db import UserCredential
from app.core.crypto import decrypt
from app.config import settings

TIMEOUT = 60


class NoCredentialError(Exception):
    pass


async def complete(prompt: str, credential: Optional[UserCredential] = None) -> str:
    if credential is None:
        raise NoCredentialError("No active AI credential configured. Go to Credentials and activate one.")

    key = decrypt(credential.api_key_encrypted, settings.SECRET_KEY) if credential.api_key_encrypted else ""

    if credential.provider == "anthropic":
        return await _anthropic(prompt, credential.model, key)

    if credential.provider == "gemini":
        return await _gemini(prompt, credential.model, key)

    if credential.provider == "ollama":
        return await _ollama(prompt, credential.model, credential.base_url or settings.OLLAMA_BASE_URL)

    # OpenAI-compatible: openai, groq, mistral, custom
    base_urls = {
        "openai":  "https://api.openai.com/v1",
        "groq":    "https://api.groq.com/openai/v1",
        "mistral": "https://api.mistral.ai/v1",
    }
    base = credential.base_url or base_urls.get(credential.provider, "")
    return await _openai_compat(prompt, credential.model, key, base)


# ── Provider implementations ──────────────────────────────────────────────────

async def _anthropic(prompt: str, model: str, api_key: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": model, "max_tokens": 2048, "messages": [{"role": "user", "content": prompt}]},
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]


async def _openai_compat(prompt: str, model: str, api_key: str, base_url: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _gemini(prompt: str, model: str, api_key: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


async def _ollama(prompt: str, model: str, base_url: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
        )
        r.raise_for_status()
        return r.json()["message"]["content"]
