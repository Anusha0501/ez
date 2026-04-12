"""
Fault-tolerant orchestrator for robust multi-agent execution.
"""

import logging
from typing import Dict, Any, List

from .orchestrator import Orchestrator
from utils.safe_executor import (
    safe_execute,
    create_minimal_pptx_fallback,
    log_agent_step,
)


class FaultTolerantOrchestrator(Orchestrator):
    """Enhanced orchestrator with fault tolerance and fallback logic."""

    # Streamlit / robust path: parse → insights → storyline → slide plans, then PPTX directly
    # (skips classifier, visual transform, chart decision, layout engine — use CLI for full pipeline).

    @staticmethod
    def _document_body(parser_output: Dict[str, Any]) -> Dict[str, Any]:
        """Inner markdown structure from ParserAgent output (elements, sections, title)."""
        if not parser_output or not isinstance(parser_output, dict):
            return {}
        inner = parser_output.get("parsed_data")
        return inner if isinstance(inner, dict) else {}

    def __init__(self, agents: Dict[str, Any]):
        super().__init__(agents)
        self.execution_logs = []
        self.logger = logging.getLogger("fault_tolerant_orchestrator")

    def execute_workflow_robust(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a reduced pipeline with fallbacks and write PPTX to output_path."""
        self.execution_logs = []

        try:
            log_agent_step("Parser Agent", "Starting markdown parsing", logs=self.execution_logs)
            parsed_data = self.agents["parser_agent"].process(input_data)
            log_agent_step("Parser Agent", "Completed successfully", logs=self.execution_logs)

            insights_data = self._execute_insight_with_fallback(parsed_data)
            storyline_data = self._execute_storyline_with_fallback(parsed_data, insights_data)
            slide_plans_data = self._execute_slide_planning_with_fallback(
                parsed_data, insights_data, storyline_data
            )

            final_data = self._generate_final_presentation(slide_plans_data, parsed_data, input_data)
            return final_data

        except Exception as e:
            self.logger.error(f"Critical error in workflow: {str(e)}")
            try:
                return self._write_emergency_pptx(input_data)
            except Exception as e2:
                self.logger.error(f"Emergency PPTX write failed: {str(e2)}")
                return {}
    
    def _execute_insight_with_fallback(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute insight agent with fallback logic."""
        def fallback_insight(data: Dict[str, Any]) -> Dict[str, Any]:
            body = FaultTolerantOrchestrator._document_body(data)
            sections = body.get("sections", [])
            elements = body.get("elements", [])

            return {
                "insights": [
                    {"text": f"Document has {len(sections)} sections", "importance": "medium"},
                    {"text": f"Document has {len(elements)} elements", "importance": "low"},
                ],
                "executive_summary": {
                    "key_points": [f"Overview of {len(sections)} sections"],
                    "themes": ["Document structure"],
                },
                "themes": [{"text": "Document Analysis", "importance": "high"}],
                "metrics": [],
                "analysis_metadata": {"fallback_used": True},
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
        def fallback_storyline(data: Dict[str, Any]) -> Dict[str, Any]:
            body = data.get("parsed_data", {})
            n_sections = len(body.get("sections", []))
            return {
                "introduction": 2,
                "summary": 1,
                "analysis": max(3, n_sections),
                "strategy": max(2, n_sections),
                "implementation": max(1, n_sections),
                "conclusion": 2,
                "narrative_flow": [
                    "Overview",
                    "Key Points",
                    "Analysis",
                    "Strategy",
                    "Implementation",
                    "Conclusion",
                ],
                "key_themes": [{"text": "Document Overview", "importance": "high"}],
                "structure": [{"title": "Introduction", "slide_number": 1}],
                "storyline_metadata": {"fallback_used": True},
            }
        
        return safe_execute(
            "Storyline Agent",
            self.agents["storyline_agent"].process,
            {"parsed_data": self._document_body(parsed_data), "insights": insights_data},
            fallback_storyline,
            self.execution_logs
        )
    
    def _execute_slide_planning_with_fallback(self, parsed_data: Dict[str, Any], insights_data: Dict[str, Any], storyline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute slide planning agent with fallback logic."""
        def fallback_slide_plans(data: Dict[str, Any]) -> Dict[str, Any]:
            body = FaultTolerantOrchestrator._document_body(data.get("parsed_data", {}))
            sections = body.get("sections", [])
            slide_plans = []
            for i, section in enumerate(sections[:10]):
                if not isinstance(section, dict):
                    continue
                title = section.get("title", f"Slide {i + 1}")
                content = section.get("content", "")
                slide_plans.append({
                    "slide_number": i + 1,
                    "title": title,
                    "type": "content",
                    "content_blocks": [{"type": "text", "content": content}],
                })
            if not slide_plans:
                slide_plans = [{
                    "slide_number": 1,
                    "title": body.get("title", "Presentation"),
                    "type": "content",
                    "content_blocks": [{"type": "text", "content": "Generated from markdown"}],
                }]
            return {"slide_plans": slide_plans, "planning_metadata": {"fallback_used": True}}
        
        return safe_execute(
            "Slide Planning Agent",
            self.agents["slide_planning_agent"].process,
            {"parsed_data": self._document_body(parsed_data), "insights": insights_data, "storyline": storyline_data},
            fallback_slide_plans,
            self.execution_logs
        )
    
    def _slide_plans_to_layout_slides(self, slide_plans_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map slide plans to PPTXGeneratorAgent layout_data.layout_data entries."""
        plans = slide_plans_data.get("slide_plans", []) or []
        out: List[Dict[str, Any]] = []
        for i, plan in enumerate(plans):
            if not isinstance(plan, dict):
                continue
            title = plan.get("title", f"Slide {i + 1}")
            content: List[str] = []
            for block in plan.get("content_blocks", []) or []:
                if isinstance(block, dict):
                    text = block.get("content") or block.get("text") or ""
                    if text:
                        content.append(str(text))
                elif block is not None:
                    content.append(str(block))
            if not content:
                km = plan.get("key_message")
                content = [str(km)] if km else [" "]
            out.append({"title": title, "content": content, "slide_type": "mixed"})
        return out

    def _write_emergency_pptx(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Last-resort PPTX from minimal slide dicts."""
        output_path = input_data.get("output_path", "output.pptx")
        minimal = create_minimal_pptx_fallback(input_data)
        layout_slides: List[Dict[str, Any]] = []
        for s in minimal.get("slides", []) or []:
            if not isinstance(s, dict):
                continue
            raw = s.get("content", [])
            if isinstance(raw, list):
                content = [str(x) for x in raw]
            else:
                content = [str(raw)] if raw else [" "]
            layout_slides.append({
                "title": s.get("title", "Slide"),
                "content": content or [" "],
                "slide_type": s.get("type", "mixed"),
            })
        if not layout_slides:
            layout_slides = [{"title": "Presentation", "content": [" "], "slide_type": "title"}]
        return self.agents["pptx_generator_agent"].process({
            "layout_data": {"layout_data": layout_slides},
            "chart_data": {"chart_specifications": []},
            "storyline": {},
            "output_path": output_path,
        })

    def _generate_final_presentation(
        self,
        slide_plans_data: Dict[str, Any],
        parsed_data: Dict[str, Any],
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Write PPTX from slide plans (robust reduced pipeline)."""
        output_path = input_data.get("output_path", "output.pptx")
        body = self._document_body(parsed_data)
        log_agent_step("PPTX Generator", "Creating final presentation", logs=self.execution_logs)

        try:
            layout_slides = self._slide_plans_to_layout_slides(slide_plans_data)
            if not layout_slides:
                return self._write_emergency_pptx(input_data)

            result = self.agents["pptx_generator_agent"].process({
                "layout_data": {"layout_data": layout_slides},
                "chart_data": {"chart_specifications": []},
                "storyline": {},
                "output_path": output_path,
            })
            log_agent_step("PPTX Generator", "Completed successfully", logs=self.execution_logs)
            if isinstance(result, dict):
                meta = result.setdefault("generation_metadata", {})
                meta["generation_method"] = "robust_reduced_pipeline"
                meta.setdefault("title_hint", body.get("title", "Generated Presentation"))
            return result

        except Exception as e:
            self.logger.error(f"Error in final presentation generation: {str(e)}")
            return self._write_emergency_pptx(input_data)

    def get_execution_logs(self) -> List[str]:
        """Get all execution logs."""
        return self.execution_logs
