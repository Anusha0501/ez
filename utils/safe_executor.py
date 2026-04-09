"""
Safe execution utilities for fault-tolerant multi-agent system.
"""

import logging
from typing import Dict, Any, List, Callable, Optional
import time
import random


def safe_execute(agent_name: str, agent_func: Callable, input_data: Dict[str, Any], 
               fallback_func: Callable, logs: List[str]) -> Dict[str, Any]:
    """Safely execute an agent with fallback logic."""
    try:
        result = agent_func(input_data)
        
        # Validate result
        if result is None or result == {}:
            raise Exception("Empty result from agent")
        
        logs.append(f"✅ {agent_name} completed successfully")
        return result
        
    except Exception as e:
        logs.append(f"⚠ {agent_name} failed: {str(e)} → using fallback")
        logging.warning(f"Agent {agent_name} failed, using fallback: {str(e)}")
        return fallback_func(input_data)


def call_gemini_with_retry(model, prompt: str, max_retries: int = 3) -> Optional[str]:
    """Call Gemini with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            
            # Check if response is valid
            if response and response.text:
                logging.info(f"Gemini call attempt {attempt + 1}/{max_retries} succeeded")
                return response.text
            
        except Exception as e:
            logging.error(f"Gemini API error on attempt {attempt + 1}: {str(e)}")
            
            # If last attempt, return None
            if attempt == max_retries - 1:
                logging.error(f"All {max_retries} attempts failed")
                return None
            
            # Wait before retry (exponential backoff)
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            logging.info(f"Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
    
    return None


def chunk_text(text: str, chunk_size: int = 5000) -> List[str]:
    """Split text into chunks for processing large inputs."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks


def validate_gemini_output(output: Any, agent_name: str) -> bool:
    """Validate Gemini output is not empty and has expected structure."""
    if output is None:
        logging.error(f"{agent_name}: Gemini returned None")
        return False
    
    if isinstance(output, str):
        if not output.strip():
            logging.error(f"{agent_name}: Gemini returned empty string")
            return False
        return True
    
    if isinstance(output, dict):
        if not output:
            logging.error(f"{agent_name}: Gemini returned empty dict")
            return False
        return True
    
    return True


def create_minimal_pptx_fallback(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create minimal PPTX structure when all agents fail."""
    return {
        "slides": [
            {
                "slide_number": 1,
                "title": input_data.get("title", "Untitled Presentation"),
                "content": ["Auto-generated presentation"],
                "type": "title"
            },
            {
                "slide_number": 2,
                "title": "Overview",
                "content": ["System generated this presentation automatically"],
                "type": "content"
            }
        ],
        "metadata": {
            "total_slides": 2,
            "generation_method": "minimal_fallback",
            "agent_failures": True
        }
    }


def log_agent_step(agent_name: str, step: str, details: Optional[Dict] = None, logs: Optional[List[str]] = None):
    """Log agent step with details."""
    message = f"{agent_name}: {step}"
    if details:
        message += f" - {details}"
    
    logging.info(message)
    if logs is not None:
        logs.append(message)
