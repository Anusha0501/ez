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
        if not self.api_key:
            self.logger.warning("GEMINI_API_KEY environment variable not found - some features may not work")
            return

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a text response from Gemini."""
        if not self.api_key or self.model is None:
            self.logger.warning("Cannot generate response: Gemini API key not configured")
            return "API key not configured - response generation unavailable"
        
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
                                   output_schema: Optional[Dict] = None, 
                                   max_retries: int = 3) -> Dict[str, Any]:
        """Generate a structured JSON response from Gemini with retry logic."""
        if not self.api_key or self.model is None:
            self.logger.warning("Cannot generate structured response: Gemini API key not configured")
            return {}

        for attempt in range(max_retries):
            try:
                # Build the full prompt
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
                else:
                    full_prompt = prompt
                
                response = self.model.generate_content(full_prompt)
                
                # Check if response is valid
                if response and response.text:
                    try:
                        # Try to parse as JSON
                        parsed_response = json.loads(response.text)
                        return parsed_response
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try to extract with regex
                        import re
                        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                        if json_match:
                            try:
                                return json.loads(json_match.group(0))
                            except:
                                pass
                
                # Log retry attempt
                self.logger.info(f"Gemini call attempt {attempt + 1}/{max_retries}")
                
                # If we got a valid response, return it
                if response and response.text:
                    return response.text
            
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {response.text}")
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
