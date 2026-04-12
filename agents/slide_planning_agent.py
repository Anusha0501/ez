"""
Slide Planning Agent - Uses Gemini to create detailed plans for each slide.
"""

import json
import logging
from typing import Dict, Any, List

from core.agent import GeminiAgent
from core.models import SlidePlan


class SlidePlanningAgent(GeminiAgent):
    """Agent responsible for creating detailed plans for each slide."""
    
    def __init__(self, gemini_client):
        system_prompt = """You are an expert presentation designer and content strategist. 
        Your task is to create detailed, actionable plans for each slide in a presentation.
        
        For each slide, you must provide:
        1. A compelling, concise title
        2. The key message (what the audience should remember)
        3. Content blocks (specific content to include)
        4. Visual elements (how to visualize the content)
        5. Chart data (if applicable)
        
        Key principles:
        - One main idea per slide
        - Limit text to 6 lines maximum
        - Prefer visuals over text
        - Use data visualizations when numbers are involved
        - Ensure logical flow between slides
        
        Always respond in valid JSON format with the specified schema."""
        
        super().__init__("slide_planning_agent", gemini_client, system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed plans for each slide."""
        try:
            self.log_reasoning("start", "Starting slide planning")
            
            # Handle both dict and list inputs safely
            storyline = input_data.get("storyline", {})
            if isinstance(storyline, list):
                storyline = storyline[0] if len(storyline) > 0 else {}
            # Ensure storyline is a dict
            if not isinstance(storyline, dict):
                storyline = {}
            
            insights = input_data.get("insights", {})
            if isinstance(insights, list):
                insights = insights[0] if len(insights) > 0 else {}
            # Ensure insights is a dict
            if not isinstance(insights, dict):
                insights = {}
            
            if not storyline:
                raise ValueError("No storyline provided")
            
            # Prepare context for slide planning
            planning_context = self._prepare_planning_context(storyline, insights)
            
            self.log_reasoning("analyze_structure", "Analyzing storyline for slide planning", {
                "slide_count": storyline.get("slide_count", 0),
                "structure_items": len(storyline.get("structure", [])),
                "key_themes": len(storyline.get("key_themes", []))
            })
            
            # Create plans for each slide
            self.log_reasoning("create_plans", "Creating detailed slide plans")
            slide_plans = self._create_slide_plans(planning_context)
            
            # Validate and optimize plans
            self.log_reasoning("validate_plans", "Validating and optimizing slide plans")
            validated_plans = self._validate_and_optimize_plans(slide_plans, planning_context)
            
            # Create planning summary
            self.log_reasoning("create_summary", "Creating planning summary")
            planning_summary = self._create_planning_summary(validated_plans)
            
            output = {
                "slide_plans": validated_plans,
                "planning_summary": planning_summary,
                "planning_metadata": {
                    "total_slides": len(validated_plans),
                    "slides_with_charts": sum(1 for plan in validated_plans if plan.get("chart_data")),
                    "slides_with_visuals": sum(1 for plan in validated_plans if plan.get("visual_elements")),
                    "avg_content_blocks": sum(len(plan.get("content_blocks", [])) for plan in validated_plans) / len(validated_plans) if validated_plans else 0,
                    "text_heavy_slides": self._identify_text_heavy_slides(validated_plans)
                }
            }
            
            self.log_reasoning("complete", "Successfully created slide plans", {
                "total_plans": len(validated_plans),
                "charts_planned": output["planning_metadata"]["slides_with_charts"],
                "visuals_planned": output["planning_metadata"]["slides_with_visuals"]
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in slide planning agent: {str(e)}")
            raise
    
    def _prepare_planning_context(self, storyline: Dict, insights: Dict) -> str:
        """Prepare comprehensive context for slide planning."""
        context_parts = []
        
        # Add storyline overview
        slide_count = storyline.get("slide_count", 0)
        storyline_metadata = storyline.get("storyline_metadata", {})
        if isinstance(storyline_metadata, list):
            storyline_metadata = storyline_metadata[0] if len(storyline_metadata) > 0 else {}
        main_message = storyline_metadata.get("main_message", "")
        
        context_parts.append(f"Presentation Overview:")
        context_parts.append(f"- Total Slides: {slide_count}")
        if main_message:
            context_parts.append(f"- Main Message: {main_message}")
        
        # Add presentation type and audience
        presentation_type = storyline_metadata.get("presentation_type", "")
        target_audience = storyline_metadata.get("target_audience", "")
        
        if presentation_type:
            context_parts.append(f"- Presentation Type: {presentation_type}")
        if target_audience:
            context_parts.append(f"- Target Audience: {target_audience}")
        
        # Add key themes
        key_themes = storyline.get("key_themes", [])
        if key_themes:
            context_parts.append(f"\\nKey Themes to Emphasize:")
            for theme in key_themes:
                context_parts.append(f"- {theme}")
        
        # Add detailed structure
        structure = storyline.get("structure", [])
        if structure:
            context_parts.append(f"\\nSlide Structure:")
            for slide_info in structure:
                if isinstance(slide_info, dict):
                    slide_num = slide_info.get("slide_number", 0)
                    title = slide_info.get("title", "")
                    narrative_purpose = slide_info.get("narrative_purpose", "")
                    slide_type = slide_info.get("slide_type", "")
                    context_parts.append(f"Slide {slide_num}: {title}")
                    context_parts.append(f"  Type: {slide_type}")
                    context_parts.append(f"  Purpose: {narrative_purpose}")
                else:
                    # Handle non-dict slide_info
                    context_parts.append(f"Slide: {str(slide_info)}")
        
        # Add key insights
        insights_list = insights.get("insights", [])
        if insights_list:
            context_parts.append(f"\\nKey Insights to Include:")
            for insight in insights_list[:5]:  # Limit to top 5 insights
                if isinstance(insight, dict):
                    insight_text = insight.get("text", "")
                    importance = insight.get("importance", 0)
                    context_parts.append(f"- {insight_text} (importance: {importance})")
                else:
                    # Handle non-dict insight
                    context_parts.append(f"- {str(insight)}")
        
        # Add metrics for potential charts
        metrics = insights.get("metrics", [])
        if metrics:
            context_parts.append(f"\\nAvailable Metrics for Charts:")
            for metric in metrics[:5]:  # Limit to top 5 metrics
                if isinstance(metric, dict):
                    metric_name = metric.get("name", "")
                    metric_value = metric.get("value", "")
                    context_parts.append(f"- {metric_name}: {metric_value}")
                else:
                    # Handle non-dict metric
                    context_parts.append(f"- {str(metric)}")
        
        # Add recommendations
        executive_summary = insights.get("executive_summary", {})
        if isinstance(executive_summary, list):
            executive_summary = executive_summary[0] if len(executive_summary) > 0 else {}
        recommendations = executive_summary.get("recommendations", [])
        if recommendations:
            context_parts.append(f"\\nKey Recommendations:")
            for rec in recommendations:
                context_parts.append(f"- {rec}")
        
        return "\\n".join(context_parts)
    
    def _create_slide_plans(self, planning_context: str) -> List[Dict[str, Any]]:
        """Create detailed plans for each slide using Gemini."""
        prompt = f"""Based on the planning context below, create detailed plans for each slide.
        For each slide, provide:
        1. title: Compelling, concise title
        2. key_message: The main takeaway for this slide
        3. content_blocks: Array of content items (max 6 total text lines)
        4. visual_elements: Array of visual elements to include
        5. chart_data: Chart specification if applicable
        
        Planning Context:
        {planning_context}
        
        Guidelines:
        - Keep text minimal (max 6 lines total per slide)
        - Always consider visual representation first
        - Use charts for any numerical data
        - Create flow diagrams for processes
        - Use comparison grids for comparisons
        - Each slide should have ONE clear purpose
        
        Respond with JSON array of slide plans."""
        
        output_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "key_message": {"type": "string"},
                    "content_blocks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "visual_elements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "position": {"type": "string"}
                            }
                        }
                    },
                    "chart_data": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "title": {"type": "string"},
                            "data": {"type": "object"}
                        }
                    }
                },
                "required": ["title", "key_message", "content_blocks", "visual_elements"]
            }
        }
        
        try:
            response = self.call_gemini(prompt, output_schema)
            if isinstance(response, list):
                return response
        except Exception as e:
            self.logger.error(f"Error calling Gemini for slide planning: {str(e)}")
        
        # Fallback: create basic plans
        return self._create_fallback_plans(planning_context)
    
    def _create_fallback_plans(self, planning_context: str) -> List[Dict[str, Any]]:
        """Create basic fallback plans if Gemini fails."""
        # Extract slide count from context
        import re
        slide_count_match = re.search(r'Total Slides: (\d+)', planning_context)
        slide_count = int(slide_count_match.group(1)) if slide_count_match else 12
        
        plans = []
        
        # Title slide
        plans.append({
            "title": "Title Slide",
            "key_message": "Introduction to the presentation",
            "content_blocks": [
                {"type": "title", "content": "Presentation Title"},
                {"type": "subtitle", "content": "Subtitle or tagline"}
            ],
            "visual_elements": [],
            "chart_data": None
        })
        
        # Agenda slide
        plans.append({
            "title": "Agenda",
            "key_message": "Overview of what will be covered",
            "content_blocks": [
                {"type": "bullet", "content": "Executive Summary"},
                {"type": "bullet", "content": "Current Situation"},
                {"type": "bullet", "content": "Key Findings"},
                {"type": "bullet", "content": "Recommendations"},
                {"type": "bullet", "content": "Next Steps"}
            ],
            "visual_elements": [
                {"type": "simple_list", "description": "Clean bullet list layout", "position": "center"}
            ],
            "chart_data": None
        })
        
        # Content slides
        for i in range(slide_count - 2):
            slide_num = i + 3
            plans.append({
                "title": f"Key Point {slide_num - 2}",
                "key_message": f"Important insight or finding {slide_num - 2}",
                "content_blocks": [
                    {"type": "heading", "content": f"Main Point {slide_num - 2}"},
                    {"type": "bullet", "content": "Supporting point 1"},
                    {"type": "bullet", "content": "Supporting point 2"},
                    {"type": "bullet", "content": "Key takeaway"}
                ],
                "visual_elements": [
                    {"type": "simple_layout", "description": "Clean text layout", "position": "standard"}
                ],
                "chart_data": None
            })
        
        return plans[:slide_count]
    
    def _validate_and_optimize_plans(self, slide_plans: List[Dict[str, Any]], planning_context: str) -> List[Dict[str, Any]]:
        """Validate and optimize slide plans."""
        validated_plans = []
        
        for i, plan in enumerate(slide_plans):
            # Validate required fields
            if not all(key in plan for key in ["title", "key_message", "content_blocks", "visual_elements"]):
                self.logger.warning(f"Slide {i+1} missing required fields, using fallback")
                plan = self._create_minimal_plan(i+1)
            
            # Optimize content blocks
            content_blocks = plan.get("content_blocks", [])
            if len(content_blocks) > 6:
                # Merge or truncate content blocks
                plan["content_blocks"] = content_blocks[:6]
                self.logger.info(f"Truncated content blocks for slide {i+1} to 6 items")
            
            # Ensure visual elements are appropriate
            visual_elements = plan.get("visual_elements", [])
            if not visual_elements and plan.get("content_blocks"):
                # Add basic visual element
                plan["visual_elements"] = [
                    {"type": "text_layout", "description": "Standard text layout", "position": "center"}
                ]
            
            # Validate chart data
            chart_data = plan.get("chart_data")
            if chart_data and not isinstance(chart_data, dict):
                plan["chart_data"] = None
                self.logger.warning(f"Invalid chart data for slide {i+1}, removed")
            
            validated_plans.append(plan)
        
        return validated_plans
    
    def _create_minimal_plan(self, slide_number: int) -> Dict[str, Any]:
        """Create a minimal valid slide plan."""
        return {
            "title": f"Slide {slide_number}",
            "key_message": f"Key message for slide {slide_number}",
            "content_blocks": [
                {"type": "heading", "content": f"Main Point {slide_number}"}
            ],
            "visual_elements": [
                {"type": "basic_layout", "description": "Basic layout", "position": "standard"}
            ],
            "chart_data": None
        }
    
    def _create_planning_summary(self, slide_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of the planning results."""
        total_slides = len(slide_plans)
        slides_with_charts = sum(1 for plan in slide_plans if plan.get("chart_data"))
        slides_with_visuals = sum(1 for plan in slide_plans if plan.get("visual_elements"))
        
        # Analyze content types
        content_types = {}
        for plan in slide_plans:
            for block in plan.get("content_blocks", []):
                block_type = block.get("type", "unknown")
                content_types[block_type] = content_types.get(block_type, 0) + 1
        
        # Analyze visual types
        visual_types = {}
        for plan in slide_plans:
            for visual in plan.get("visual_elements", []):
                visual_type = visual.get("type", "unknown")
                visual_types[visual_type] = visual_types.get(visual_type, 0) + 1
        
        return {
            "total_slides_planned": total_slides,
            "slides_requiring_charts": slides_with_charts,
            "slides_with_visual_elements": slides_with_visuals,
            "content_distribution": content_types,
            "visual_element_distribution": visual_types,
            "planning_quality_score": self._calculate_planning_quality(slide_plans)
        }
    
    def _calculate_planning_quality(self, slide_plans: List[Dict[str, Any]]) -> float:
        """Calculate a quality score for the planning."""
        score = 0.0
        total_slides = len(slide_plans)
        
        if total_slides == 0:
            return 0.0
        
        # Check for appropriate content length
        appropriate_content_slides = sum(
            1 for plan in slide_plans 
            if 1 <= len(plan.get("content_blocks", [])) <= 6
        )
        score += (appropriate_content_slides / total_slides) * 0.3
        
        # Check for visual elements
        slides_with_visuals = sum(
            1 for plan in slide_plans 
            if plan.get("visual_elements")
        )
        score += (slides_with_visuals / total_slides) * 0.3
        
        # Check for key messages
        slides_with_key_messages = sum(
            1 for plan in slide_plans 
            if plan.get("key_message") and len(plan.get("key_message", "")) > 10
        )
        score += (slides_with_key_messages / total_slides) * 0.2
        
        # Check for appropriate titles
        slides_with_good_titles = sum(
            1 for plan in slide_plans 
            if plan.get("title") and len(plan.get("title", "")) > 3
        )
        score += (slides_with_good_titles / total_slides) * 0.2
        
        return round(score, 2)
    
    def _identify_text_heavy_slides(self, slide_plans: List[Dict[str, Any]]) -> List[int]:
        """Identify slides that are too text-heavy."""
        text_heavy_slides = []
        
        for i, plan in enumerate(slide_plans):
            content_blocks = plan.get("content_blocks", [])
            total_text_length = sum(
                len(block.get("content", "")) 
                for block in content_blocks
            )
            
            # Consider text-heavy if more than 300 characters total
            if total_text_length > 300:
                text_heavy_slides.append(i + 1)  # Slide numbers are 1-based
        
        return text_heavy_slides
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the slide planning output."""
        if not output:
            return False
        
        required_keys = ["slide_plans", "planning_summary", "planning_metadata"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in slide planning output: {key}")
                return False
        
        # Validate slide plans
        slide_plans = output.get("slide_plans", [])
        if not isinstance(slide_plans, list):
            self.logger.error("slide_plans is not a list")
            return False
        
        if len(slide_plans) == 0:
            self.logger.error("No slide plans created")
            return False
        
        # Validate each plan
        for i, plan in enumerate(slide_plans):
            if not isinstance(plan, dict):
                self.logger.error(f"Slide plan {i} is not a dictionary")
                return False
            
            required_plan_keys = ["title", "key_message", "content_blocks", "visual_elements"]
            for key in required_plan_keys:
                if key not in plan:
                    self.logger.error(f"Slide plan {i} missing required key: {key}")
                    return False
        
        return True
