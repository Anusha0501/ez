"""
Google Gemini client for AI reasoning.
"""

import time
import random
import json
import logging
import os
from typing import Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv
from utils.groq_client import GroqClient

load_dotenv()


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.logger = logging.getLogger("gemini_client")
        # Explicit api_key (including "") overrides env; only None reads GEMINI_API_KEY.
        if api_key is not None:
            self.api_key = api_key or None
        else:
            self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        self.groq_client = GroqClient()
        if not self.api_key:
            self.logger.warning("GEMINI_API_KEY environment variable not found - some features may not work")
            return

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if system_prompt:
            return f"System: {system_prompt}\n\nUser: {prompt}"
        return prompt

    def _parse_structured_text(self, text: str) -> Dict[str, Any]:
        """Parse structured JSON-like text into a Python object."""
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
        """Primary LLM router: Gemini -> Groq -> deterministic fallback."""
        try:
            if logs is not None:
                logs.append("Using Gemini")
            self.logger.info("Using Gemini")
            if not self.api_key or self.model is None:
                raise RuntimeError("Gemini not configured")
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text
            raise RuntimeError("Gemini returned empty response")

        except Exception as gemini_error:
            if logs is not None:
                logs.append(f"Gemini failed: {gemini_error}")
                logs.append("Switching to Groq")
            self.logger.warning(f"Gemini failed → switching to Groq ({str(gemini_error)})")
            self.logger.info("Switching to Groq")

            try:
                groq_text = self.groq_client.call_groq(prompt)
                if groq_text:
                    return groq_text
                raise RuntimeError("Groq returned empty response")
            except Exception as groq_error:
                if logs is not None:
                    logs.append(f"Groq failed: {groq_error}")
                    logs.append("Using fallback")
                self.logger.warning(f"Groq failed → using fallback ({str(groq_error)})")
                self.logger.info("Using fallback")
                return "Auto-generated content based on document structure. (API key not configured)"
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a text response from Gemini."""
        full_prompt = self._build_prompt(prompt, system_prompt)
        return self.call_llm(full_prompt)
    
    def generate_structured_response(self, prompt: str, system_prompt: Optional[str] = None, 
                                   output_schema: Optional[Dict] = None, 
                                   max_retries: int = 3) -> Dict[str, Any]:
        """Generate a structured JSON response from Gemini with retry logic."""
        full_prompt = self._build_prompt(prompt, system_prompt)
        if output_schema:
            full_prompt += f"\n\nReturn strictly valid JSON matching this schema:\n{json.dumps(output_schema)}"

        llm_logs = []
        llm_text = self.call_llm(full_prompt, logs=llm_logs)
        parsed = self._parse_structured_text(llm_text)
        if parsed:
            return parsed
        self.logger.warning("Using fallback")
        return {}
    
    def test_connection(self) -> bool:
        """Test the Gemini API connection."""
        try:
            response = self.generate_response("Hello, can you respond with 'OK'?")
            return "OK" in response
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
