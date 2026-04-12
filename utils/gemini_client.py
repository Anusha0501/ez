"""
Compatibility client that now routes all LLM calls to Groq single-call mode.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

from utils.groq_client import GroqClient


class GeminiClient:
    """Backward-compatible interface; Gemini is disabled and Groq is used exclusively."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama-3.1-8b-instant"):
        self.logger = logging.getLogger("gemini_client")
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model_name if self.api_key else None
        self.groq_client = GroqClient(api_key=self.api_key, model_name=model_name)

    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if system_prompt:
            return f"System: {system_prompt}\n\nUser: {prompt}"
        return prompt

    def _parse_structured_text(self, text: str) -> Dict[str, Any]:
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except Exception:
                    return {}
        return {}

    def call_llm(self, prompt: str, logs: Optional[list] = None) -> str:
        """Groq-only router (Gemini disabled)."""
        if logs is not None:
            logs.append("Using Groq (single-call mode)")
        self.logger.info("Using Groq (single-call mode)")
        if not self.api_key or self.model is None:
            return "Auto-generated content based on document structure. (API key not configured)"
        return self.groq_client.call_groq(prompt)

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        full_prompt = self._build_prompt(prompt, system_prompt)
        return self.call_llm(full_prompt)

    def generate_structured_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_schema: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        full_prompt = self._build_prompt(prompt, system_prompt)
        if output_schema:
            full_prompt += f"\n\nReturn strictly valid JSON matching this schema:\n{json.dumps(output_schema)}"

        llm_text = self.call_llm(full_prompt)
        if not self.api_key or self.model is None:
            return {}
        parsed = self._parse_structured_text(llm_text)
        return parsed if parsed else {}

    def test_connection(self) -> bool:
        try:
            response = self.generate_response("Respond with OK")
            return "OK" in response
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
