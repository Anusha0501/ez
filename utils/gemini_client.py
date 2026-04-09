"""
Google Gemini client for AI reasoning.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.logger = logging.getLogger("gemini_client")
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a text response from Gemini."""
        try:
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            else:
                full_prompt = prompt
            
            response = self.model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"Gemini API error: {str(e)}")
            raise
    
    def generate_structured_response(self, prompt: str, system_prompt: Optional[str] = None, 
                                   output_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate a structured JSON response from Gemini."""
        try:
            # Build the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            # Add JSON output instructions
            if output_schema:
                schema_instruction = f"\n\nIMPORTANT: Respond with valid JSON only. Use this schema:\n{json.dumps(output_schema, indent=2)}"
                full_prompt += schema_instruction
            else:
                full_prompt += "\n\nIMPORTANT: Respond with valid JSON only."
            
            response = self.model.generate_content(full_prompt)
            
            # Parse JSON response
            try:
                # Clean the response to extract JSON
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                return json.loads(response_text)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {response.text}")
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Gemini API error: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test the Gemini API connection."""
        try:
            response = self.generate_response("Hello, can you respond with 'OK'?")
            return "OK" in response
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
