"""
Orchestrator for the multi-agent system.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agent import BaseAgent
from .models import OrchestratorLog, Presentation


class Orchestrator:
    """Orchestrates the multi-agent workflow with feedback loops."""
    
    def __init__(self, agents: Dict[str, BaseAgent], max_iterations: int = 3):
        self.agents = agents
        self.max_iterations = max_iterations
        self.logger = logging.getLogger("orchestrator")
        self.execution_log: List[OrchestratorLog] = []
        self.intermediate_data = {}
        
    def execute_workflow(self, input_data: Dict[str, Any]) -> Presentation:
        """Execute the complete multi-agent workflow."""
        try:
            self.logger.info("Starting multi-agent workflow execution")
            
            # Step 1: Parse Markdown
            parsed_data = self._execute_agent_step(
                "parser_agent", 
                {"markdown_content": input_data.get("markdown_content", "")}
            )
            
            # Step 2: Extract Insights
            insights_data = self._execute_agent_step(
                "insight_agent",
                {"parsed_data": parsed_data}
            )
            
            # Step 3: Create Storyline
            storyline_data = self._execute_agent_step(
                "storyline_agent",
                {"parsed_data": parsed_data, "insights": insights_data}
            )
            
            # Step 4: Plan Slides
            slide_plans_data = self._execute_agent_step(
                "slide_planning_agent",
                {"storyline": storyline_data, "insights": insights_data}
            )
            
            # Step 5: Classify Slide Types
            classified_slides = self._execute_agent_step(
                "slide_classifier_agent",
                {"slide_plans": slide_plans_data}
            )
            
            # Step 6: Visual Transformation (with feedback loop)
            visual_data = self._execute_with_feedback(
                "visual_transformation_agent",
                {"classified_slides": classified_slides, "parsed_data": parsed_data},
                validation_func=self._validate_visual_output
            )
            
            # Step 7: Chart Decisions
            chart_data = self._execute_agent_step(
                "chart_decision_agent",
                {"visual_data": visual_data, "parsed_data": parsed_data}
            )
            
            # Step 8: Layout Engine
            layout_data = self._execute_agent_step(
                "layout_engine",
                {"visual_data": visual_data, "chart_data": chart_data}
            )
            
            # Step 9: Generate PPTX
            presentation = self._execute_agent_step(
                "pptx_generator_agent",
                {
                    "layout_data": layout_data,
                    "chart_data": chart_data,
                    "storyline": storyline_data,
                    "output_path": input_data.get("output_path", "output.pptx")
                }
            )
            
            self.logger.info("Multi-agent workflow completed successfully")
            return presentation
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            raise
    
    def _execute_agent_step(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent step."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        self.logger.info(f"Executing {agent_name}")
        
        try:
            # Execute agent
            agent_output = agent.execute(input_data)
            
            # Log the execution
            log_entry = OrchestratorLog(
                step=len(self.execution_log) + 1,
                agent=agent_name,
                input=input_data,
                output=agent_output.output_data,
                reasoning=agent_output.reasoning,
                success=agent_output.confidence > 0.5
            )
            
            self.execution_log.append(log_entry)
            self.intermediate_data[agent_name] = agent_output.output_data
            
            if not log_entry.success:
                raise RuntimeError(f"Agent {agent_name} failed with low confidence")
            
            return agent_output.output_data
            
        except Exception as e:
            # Log failure
            log_entry = OrchestratorLog(
                step=len(self.execution_log) + 1,
                agent=agent_name,
                input=input_data,
                output={},
                reasoning=f"Error: {str(e)}",
                success=False,
                errors=[str(e)]
            )
            
            self.execution_log.append(log_entry)
            raise
    
    def _execute_with_feedback(self, agent_name: str, input_data: Dict[str, Any], 
                             validation_func: callable) -> Dict[str, Any]:
        """Execute agent with feedback loop for validation."""
        for iteration in range(self.max_iterations):
            try:
                self.logger.info(f"Executing {agent_name} - iteration {iteration + 1}")
                
                # Add iteration info to input
                iteration_input = {
                    **input_data,
                    "iteration": iteration + 1,
                    "previous_output": self.intermediate_data.get(agent_name) if iteration > 0 else None
                }
                
                # Execute agent
                output = self._execute_agent_step(agent_name, iteration_input)
                
                # Validate output
                validation_result = validation_func(output)
                
                if validation_result["valid"]:
                    self.logger.info(f"{agent_name} output validated successfully")
                    return output
                else:
                    self.logger.warning(f"{agent_name} output validation failed: {validation_result['reason']}")
                    if iteration == self.max_iterations - 1:
                        # Last iteration, use the output anyway
                        self.logger.warning(f"Using {agent_name} output despite validation failure")
                        return output
                    
                    # Add feedback to next iteration
                    input_data["feedback"] = validation_result["feedback"]
                    
            except Exception as e:
                self.logger.error(f"Error in {agent_name} iteration {iteration + 1}: {str(e)}")
                if iteration == self.max_iterations - 1:
                    raise
                continue
        
        raise RuntimeError(f"Failed to execute {agent_name} after {self.max_iterations} iterations")
    
    def _validate_visual_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate visual transformation output."""
        try:
            if not output or "visual_elements" not in output:
                return {
                    "valid": False,
                    "reason": "Missing visual_elements in output",
                    "feedback": "Please include visual_elements in your response"
                }
            
            visual_elements = output["visual_elements"]
            
            # Check if slides are too text-heavy
            text_heavy_slides = []
            for i, element in enumerate(visual_elements):
                if isinstance(element, dict):
                    text_content = element.get("text_content", "")
                    if len(text_content.split()) > 50:  # More than 50 words
                        text_heavy_slides.append(i)
            
            if text_heavy_slides:
                return {
                    "valid": False,
                    "reason": f"Slides {text_heavy_slides} are too text-heavy",
                    "feedback": f"Convert text to visuals for slides {text_heavy_slides}. Use diagrams, charts, or structured layouts instead of paragraphs."
                }
            
            # Check for proper visual variety
            visual_types = [elem.get("type", "unknown") for elem in visual_elements if isinstance(elem, dict)]
            unique_types = set(visual_types)
            
            if len(unique_types) < 2 and len(visual_elements) > 3:
                return {
                    "valid": False,
                    "reason": "Insufficient visual variety",
                    "feedback": "Add more visual variety. Use different types like flow diagrams, timelines, grids, and charts."
                }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "reason": f"Validation error: {str(e)}",
                "feedback": "Fix the output format and structure"
            }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow execution."""
        total_steps = len(self.execution_log)
        successful_steps = sum(1 for log in self.execution_log if log.success)
        
        agent_performance = {}
        for log in self.execution_log:
            if log.agent not in agent_performance:
                agent_performance[log.agent] = {
                    "executions": 0,
                    "successes": 0,
                    "total_reasoning_length": 0
                }
            
            agent_performance[log.agent]["executions"] += 1
            if log.success:
                agent_performance[log.agent]["successes"] += 1
            agent_performance[log.agent]["total_reasoning_length"] += len(log.reasoning)
        
        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0,
            "agent_performance": agent_performance,
            "execution_time": self._calculate_execution_time(),
            "intermediate_data_keys": list(self.intermediate_data.keys())
        }
    
    def _calculate_execution_time(self) -> str:
        """Calculate total execution time."""
        if not self.execution_log:
            return "0s"
        
        # This is a simplified calculation
        # In a real implementation, you'd track actual timestamps
        return f"{len(self.execution_log) * 2}s"  # Estimate 2 seconds per step
    
    def save_execution_log(self, filepath: str):
        """Save the execution log to a file."""
        try:
            log_data = {
                "execution_summary": self.get_execution_summary(),
                "detailed_logs": [
                    {
                        "step": log.step,
                        "agent": log.agent,
                        "input": log.input,
                        "output": log.output,
                        "reasoning": log.reasoning,
                        "success": log.success,
                        "errors": log.errors
                    }
                    for log in self.execution_log
                ],
                "intermediate_data": self.intermediate_data
            }
            
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
            
            self.logger.info(f"Execution log saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving execution log: {str(e)}")
            raise
    
    def get_agent_reasoning(self, agent_name: str) -> List[str]:
        """Get reasoning logs for a specific agent."""
        reasoning_steps = []
        
        for log in self.execution_log:
            if log.agent == agent_name:
                reasoning_steps.append(log.reasoning)
        
        return reasoning_steps
