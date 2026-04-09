"""
Fault-tolerant orchestrator for robust multi-agent execution.
"""

import logging
from typing import Dict, Any, List, Optional
from .orchestrator import Orchestrator
from utils.safe_executor import safe_execute, call_gemini_with_retry, chunk_text, validate_gemini_output, create_minimal_pptx_fallback, log_agent_step


class FaultTolerantOrchestrator(Orchestrator):
    """Enhanced orchestrator with fault tolerance and fallback logic."""
    
    def __init__(self, agents: Dict[str, Any]):
        super().__init__(agents)
        self.execution_logs = []
        self.logger = logging.getLogger("fault_tolerant_orchestrator")
    
    def execute_workflow_robust(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow with fault tolerance and guaranteed output."""
        self.execution_logs = []
        
        try:
            # Step 1: Parse markdown (always works)
            log_agent_step("Parser Agent", "Starting markdown parsing", self.execution_logs)
            parsed_data = self.agents["parser_agent"].process(input_data)
            log_agent_step("Parser Agent", "Completed successfully", self.execution_logs)
            
            # Step 2: Extract insights with fallback
            insights_data = self._execute_insight_with_fallback(parsed_data)
            
            # Step 3: Create storyline with fallback
            storyline_data = self._execute_storyline_with_fallback(parsed_data, insights_data)
            
            # Step 4: Plan slides with fallback
            slide_plans_data = self._execute_slide_planning_with_fallback(parsed_data, insights_data, storyline_data)
            
            # Step 5: Generate final presentation
            final_data = self._generate_final_presentation(slide_plans_data, parsed_data)
            
            return final_data
            
        except Exception as e:
            self.logger.error(f"Critical error in workflow: {str(e)}")
            # Return minimal presentation even on critical failure
            return create_minimal_pptx_fallback(input_data)
    
    def _execute_insight_with_fallback(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute insight agent with fallback logic."""
        def fallback_insight(data):
            sections = data.get("sections", [])
            elements = data.get("elements", [])
            
            return {
                "insights": [
                    {"text": f"Document has {len(sections)} sections", "importance": "medium"},
                    {"text": f"Document has {len(elements)} elements", "importance": "low"}
                ],
                "executive_summary": {
                    "key_points": [f"Overview of {len(sections)} sections"],
                    "themes": ["Document structure"]
                },
                "themes": [{"text": "Document Analysis", "importance": "high"}],
                "metrics": [],
                "analysis_metadata": {"fallback_used": True}
            }
        
        return safe_execute(
            "Insight Agent",
            self.agents["insight_agent"].process,
            parsed_data,
            fallback_insight,
            self.execution_logs
        )
    
    def _execute_storyline_with_fallback(self, parsed_data: Dict[str, Any], insights_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute storyline agent with fallback logic."""
        def fallback_storyline(data):
            return {
                "introduction": 2,
                "summary": 1,
                "analysis": max(3, len(data.get("sections", []))),
                "strategy": max(2, len(data.get("sections", []))),
                "implementation": max(1, len(data.get("sections", []))),
                "conclusion": 2,
                "narrative_flow": ["Overview", "Key Points", "Analysis", "Strategy", "Implementation", "Conclusion"],
                "key_themes": [{"text": "Document Overview", "importance": "high"}],
                "structure": [{"title": "Introduction", "slide_number": 1}],
                "storyline_metadata": {"fallback_used": True}
            }
        
        return safe_execute(
            "Storyline Agent",
            self.agents["storyline_agent"].process,
            {"parsed_data": parsed_data, "insights": insights_data},
            fallback_storyline,
            self.execution_logs
        )
    
    def _execute_slide_planning_with_fallback(self, parsed_data: Dict[str, Any], insights_data: Dict[str, Any], storyline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute slide planning agent with fallback logic."""
        def fallback_slide_plans(data):
            sections = data.get("sections", [])
            return {
                "slide_plans": [
                    {
                        "slide_number": i + 1,
                        "title": section.get("title", f"Slide {i + 1}"),
                        "type": "content",
                        "content_blocks": [{"type": "text", "content": section.get("content", "")}]
                    }
                    for i, section in enumerate(sections[:10])
                ],
                "planning_metadata": {"fallback_used": True}
            }
        
        return safe_execute(
            "Slide Planning Agent",
            self.agents["slide_planning_agent"].process,
            {"parsed_data": parsed_data, "insights": insights_data, "storyline": storyline_data},
            fallback_slide_plans,
            self.execution_logs
        )
    
    def _generate_final_presentation(self, slide_plans_data: Dict[str, Any], parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final presentation from slide plans."""
        try:
            # Generate PPTX
            log_agent_step("PPTX Generator", "Creating final presentation", self.execution_logs)
            
            # Create output data structure
            output_data = {
                "slides": slide_plans_data.get("slide_plans", []),
                "metadata": {
                    "title": parsed_data.get("title", "Generated Presentation"),
                    "total_slides": len(slide_plans_data.get("slide_plans", [])),
                    "generation_method": "multi_agent_with_fallbacks"
                }
            }
            
            log_agent_step("PPTX Generator", "Completed successfully", self.execution_logs)
            return output_data
            
        except Exception as e:
            self.logger.error(f"Error in final presentation generation: {str(e)}")
            # Return basic structure
            return create_minimal_pptx_fallback(parsed_data)
    
    def get_execution_logs(self) -> List[str]:
        """Get all execution logs."""
        return self.execution_logs
