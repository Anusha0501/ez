"""
Base agent framework for the multi-agent system.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from .models import AgentOutput
from ..utils.gemini_client import GeminiClient


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, gemini_client: Optional[GeminiClient] = None):
        self.name = name
        self.gemini_client = gemini_client
        self.logger = logging.getLogger(f"agent.{name}")
        self.reasoning_log = []
        
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return output."""
        pass
    
    def log_reasoning(self, step: str, reasoning: str, data: Any = None):
        """Log reasoning steps for transparency."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "reasoning": reasoning,
            "data": data
        }
        self.reasoning_log.append(log_entry)
        self.logger.info(f"Reasoning - {step}: {reasoning}")
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the output structure."""
        return bool(output and isinstance(output, dict))
    
    def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Execute the agent with full logging."""
        start_time = datetime.now()
        
        try:
            self.log_reasoning("start", f"Starting {self.name} agent", input_data)
            
            # Process the data
            output_data = self.process(input_data)
            
            # Validate output
            if not self.validate_output(output_data):
                raise ValueError(f"Invalid output from {self.name} agent")
            
            # Create agent output
            agent_output = AgentOutput(
                agent_name=self.name,
                input_data=input_data,
                output_data=output_data,
                reasoning=json.dumps(self.reasoning_log, indent=2),
                confidence=1.0,
                timestamp=start_time.isoformat()
            )
            
            self.log_reasoning("complete", f"Successfully completed {self.name} agent")
            return agent_output
            
        except Exception as e:
            self.logger.error(f"Error in {self.name} agent: {str(e)}")
            return AgentOutput(
                agent_name=self.name,
                input_data=input_data,
                output_data={},
                reasoning=f"Error: {str(e)}",
                confidence=0.0,
                timestamp=start_time.isoformat()
            )


class GeminiAgent(BaseAgent):
    """Base class for agents that use Gemini for reasoning."""
    
    def __init__(self, name: str, gemini_client: GeminiClient, system_prompt: str):
        super().__init__(name, gemini_client)
        self.system_prompt = system_prompt
    
    def call_gemini(self, prompt: str, output_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Call Gemini with structured output."""
        try:
            self.log_reasoning("gemini_call", f"Calling Gemini with prompt: {prompt[:100]}...")
            
            response = self.gemini_client.generate_structured_response(
                prompt=prompt,
                system_prompt=self.system_prompt,
                output_schema=output_schema
            )
            
            self.log_reasoning("gemini_response", f"Received response from Gemini", response)
            return response
            
        except Exception as e:
            self.logger.error(f"Gemini API error in {self.name}: {str(e)}")
            raise
    
    def process_with_gemini(self, input_data: Dict[str, Any], prompt_template: str, 
                          output_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Process input data using Gemini with a prompt template."""
        # Format the prompt with input data
        prompt = prompt_template.format(**input_data)
        
        # Call Gemini
        return self.call_gemini(prompt, output_schema)
