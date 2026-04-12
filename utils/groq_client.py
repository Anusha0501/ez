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
try:
    import streamlit as st
except Exception:  # pragma: no cover - streamlit optional in non-UI test env
    st = None

GROQ_MODEL = "llama3-8b-8192"


class GroqClient:
    """Thin wrapper for Groq chat completions."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = GROQ_MODEL):
        self.logger = logging.getLogger("groq_client")
        self.api_key = api_key
        self.model_name = model_name
        self.client = None

    def _read_secret_key(self) -> Optional[str]:
        if self.api_key:
            return self.api_key
        if st is not None:
            try:
                key = st.secrets.get("GROQ_API_KEY")
                if key:
                    return key
            except Exception:
                pass
        return os.getenv("GROQ_API_KEY")

    def get_client(self):
        """Initialize and return a Groq client."""
        if OpenAI is None:
            raise RuntimeError("openai package not installed")
        api_key = self._read_secret_key()
        if not api_key:
            raise Exception("Missing GROQ_API_KEY")
        return OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
        )

    def call_groq(self, prompt: str) -> str:
        """Call Groq and return response text."""
        client = self.get_client()
        self.logger.info(f"Using Groq model: {self.model_name}")
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = (response.choices[0].message.content or "").strip()
            if not response_text or len(response_text.strip()) < 10:
                raise Exception("Groq returned empty response")
            return response_text
        except Exception as e:
            raise Exception(f"Groq error: {str(e)}")
