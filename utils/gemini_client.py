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
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a text response from Gemini."""
        full_prompt = self._build_prompt(prompt, system_prompt)
        if self.api_key and self.model is not None:
            try:
                self.logger.info("Using Gemini")
                response = self.model.generate_content(full_prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                self.logger.warning(f"Gemini failed → using Groq ({str(e)})")
        else:
            self.logger.warning("Gemini failed → using Groq (Gemini not configured)")

        try:
            groq_text = self.groq_client.call_groq(full_prompt)
            if groq_text:
                return groq_text
        except Exception as e:
            self.logger.warning(f"Groq failed → using fallback ({str(e)})")

        return "API key not configured - response generation unavailable"
    
    def generate_structured_response(self, prompt: str, system_prompt: Optional[str] = None, 
                                   output_schema: Optional[Dict] = None, 
                                   max_retries: int = 3) -> Dict[str, Any]:
        """Generate a structured JSON response from Gemini with retry logic."""
        full_prompt = self._build_prompt(prompt, system_prompt)
        if output_schema:
            full_prompt += f"\n\nReturn strictly valid JSON matching this schema:\n{json.dumps(output_schema)}"

        # 1) Gemini first
        if self.api_key and self.model is not None:
            for attempt in range(max_retries):
                try:
                    self.logger.info("Using Gemini")
                    response = self.model.generate_content(full_prompt)
                    parsed = self._parse_structured_text(response.text if response else "")
                    if parsed:
                        return parsed
                except Exception as e:
                    self.logger.warning(f"Gemini failed → using Groq ({str(e)})")
                    break
                self.logger.info(f"Gemini call attempt {attempt + 1}/{max_retries}")
        else:
            self.logger.warning("Gemini failed → using Groq (Gemini not configured)")

        # 2) Groq fallback
        try:
            groq_text = self.groq_client.call_groq(full_prompt)
            parsed = self._parse_structured_text(groq_text)
            if parsed:
                return parsed
            self.logger.warning("Groq failed → using fallback (unparseable response)")
        except Exception as e:
            self.logger.warning(f"Groq failed → using fallback ({str(e)})")

        # 3) Final fallback
        return {}
    
    def test_connection(self) -> bool:
        """Test the Gemini API connection."""
        try:
            response = self.generate_response("Hello, can you respond with 'OK'?")
            return "OK" in response
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
