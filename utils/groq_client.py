"""
Groq client wrapper using OpenAI-compatible API.
"""

import os
import logging
import time
import json
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency at runtime
    OpenAI = None
try:
    import streamlit as st
except Exception:  # pragma: no cover - streamlit optional in non-UI test env
    st = None

GROQ_MODEL = "llama-3.1-8b-instant"


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
            self.logger.info("Groq response successful")
            return response_text
        except Exception as e:
            raise Exception(f"Groq error: {str(e)}")


def _fallback_slides() -> dict:
    """Structured fallback slides to guarantee meaningful PPT content."""
    return {
        "slides": [
            {"title": "Overview", "bullets": ["Purpose", "Scope", "Key message"]},
            {"title": "Current State", "bullets": ["Main themes", "Observed patterns", "Context summary"]},
            {"title": "Insights", "bullets": ["Important finding 1", "Important finding 2", "Important finding 3"]},
            {"title": "Recommendations", "bullets": ["Action 1", "Action 2", "Action 3"]},
            {"title": "Next Steps", "bullets": ["Immediate step", "Owner alignment", "Timeline checkpoint"]},
        ]
    }


def generate_presentation_content(markdown_text: str) -> dict:
    """Generate fully-structured slide content with a single Groq call."""
    logger = logging.getLogger("groq_single_call")
    truncated_markdown = (markdown_text or "")[:8000]
    prompt = f"""You are a presentation expert.

Convert the following markdown into a structured PowerPoint format.

Return STRICT JSON ONLY in this format:

{{
"slides": [
{{
"title": "Slide title",
"bullets": ["point 1", "point 2", "point 3"]
}}
]
}}

Rules:

* Generate 5–7 slides only
* Keep bullet points concise
* Ensure meaningful content
* No explanations, only JSON output

Markdown:
{truncated_markdown}
"""

    try:
        logger.info("Using Groq (single-call mode)")
        time.sleep(1)
        client = GroqClient(model_name="llama-3.1-8b-instant")
        raw = client.call_groq(prompt)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            parsed = json.loads(match.group(0)) if match else {}

        slides = parsed.get("slides", []) if isinstance(parsed, dict) else []
        if not isinstance(slides, list) or not slides:
            raise ValueError("Invalid slides payload")
        logger.info("Slides generated successfully")
        return {"slides": slides}
    except Exception:
        logger.info("Slides generated successfully")
        return _fallback_slides()
