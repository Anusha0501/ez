"""
Groq client wrapper using OpenAI-compatible API.
"""

import os
import logging
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency at runtime
    OpenAI = None


class GroqClient:
    """Thin wrapper for Groq chat completions."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama3-70b-8192"):
        self.logger = logging.getLogger("groq_client")
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model_name = model_name
        self.client = None
        if OpenAI is None:
            self.logger.warning("openai package not installed; Groq fallback disabled")
            return
        if not self.api_key:
            self.logger.warning("GROQ_API_KEY not configured")
            return
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key,
        )

    def call_groq(self, prompt: str) -> str:
        """Call Groq and return response text."""
        if self.client is None:
            raise RuntimeError("Groq client not configured")

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return (response.choices[0].message.content or "").strip()
