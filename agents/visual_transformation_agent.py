"""
Visual Transformation Agent - Uses Gemini to transform text into visual elements.
"""

import json
import logging
from typing import Dict, Any, List

from ..core.agent import GeminiAgent
from ..core.models import VisualElement


class VisualTransformationAgent(GeminiAgent):
    """Agent responsible for transforming text content into visual elements."""
    
    def __init__(self, gemini_client):
        system_prompt = """You are an expert visual designer and information visualization specialist.
        Your task is to transform text-heavy content into compelling visual elements.
        
        CORE PRINCIPLE: Before placing any text, ask "Can this be visualized?"
        If YES: Convert into flow diagrams, timelines, comparison grids, or structured layouts
        If NO: Limit text to maximum 6 lines
        
        Visual Types:
        - flow: Sequential processes, decision trees, workflows
        - timeline: Chronological events, roadmaps, milestones
        - grid: Comparison tables, feature matrices, structured data
        - diagram: Conceptual relationships, hierarchies, mind maps
        - infographic: Data visualization, statistics, key metrics
        
        For each visual element, provide:
        1. Type of visualization
        2. Layout specifications (grid, positioning)
        3. Content items with their positions
        4. Visual styling recommendations
        
        Always prioritize visual representation over text.
        Respond in valid JSON format with specified schema."""
        
        super().__init__("visual_transformation_agent", gemini_client, system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform slide content into visual elements."""
        try:
            self.log_reasoning("start", "Starting visual transformation")
            
            classified_slides = input_data.get("classified_slides", [])
            parsed_data = input_data.get("parsed_data", {})
            iteration = input_data.get("iteration", 1)
            feedback = input_data.get("feedback", "")
            
            if not classified_slides:
                raise ValueError("No classified slides provided")
            
            # Prepare context for visual transformation
            transformation_context = self._prepare_transformation_context(classified_slides, parsed_data, feedback)
            
            self.log_reasoning("analyze_content", "Analyzing content for visual opportunities", {
                "total_slides": len(classified_slides),
                "iteration": iteration,
                "has_feedback": bool(feedback)
            })
            
            # Transform slides using Gemini
            self.log_reasoning("transform_slides", "Transforming slides with visual elements")
            transformed_slides = self._transform_slides_with_gemini(transformation_context, iteration)
            
            # Validate visual transformations
            self.log_reasoning("validate_transformations", "Validating visual transformations")
            validated_transformations = self._validate_visual_transformations(transformed_slides)
            
            # Optimize for visual impact
            self.log_reasoning("optimize_visuals", "Optimizing for visual impact")
            optimized_visuals = self._optimize_visual_impact(validated_transformations)
            
            # Create transformation summary
            self.log_reasoning("create_summary", "Creating transformation summary")
            transformation_summary = self._create_transformation_summary(optimized_visuals)
            
            output = {
                "visual_elements": optimized_visuals,
                "transformation_summary": transformation_summary,
                "transformation_metadata": {
                    "total_slides": len(optimized_visuals),
                    "slides_with_flow_diagrams": sum(1 for slide in optimized_visuals if self._has_visual_type(slide, "flow")),
                    "slides_with_timelines": sum(1 for slide in optimized_visuals if self._has_visual_type(slide, "timeline")),
                    "slides_with_grids": sum(1 for slide in optimized_visuals if self._has_visual_type(slide, "grid")),
                    "slides_with_diagrams": sum(1 for slide in optimized_visuals if self._has_visual_type(slide, "diagram")),
                    "text_heavy_slides": self._identify_text_heavy_slides(optimized_visuals),
                    "visual_variety_score": self._calculate_visual_variety(optimized_visuals)
                }
            }
            
            self.log_reasoning("complete", "Successfully transformed content visually", {
                "total_transformations": len(optimized_visuals),
                "visual_types_used": self._get_visual_types_used(optimized_visuals),
                "text_heavy_count": output["transformation_metadata"]["text_heavy_slides"]
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in visual transformation agent: {str(e)}")
            raise
    
    def _prepare_transformation_context(self, classified_slides: List[Dict], parsed_data: Dict, feedback: str) -> str:
        """Prepare context for visual transformation."""
        context_parts = []
        
        context_parts.append("Visual Transformation Context:")
        
        # Add feedback if provided
        if feedback:
            context_parts.append(f"Previous Feedback: {feedback}")
            context_parts.append("Please address this feedback in your transformations.")
        
        # Add slide information
        context_parts.append("\\nSlides to Transform:")
        for i, slide_info in enumerate(classified_slides):
            slide_num = slide_info.get("slide_number", i + 1)
            slide_type = slide_info.get("slide_type", "")
            
            context_parts.append(f"\\nSlide {slide_num} ({slide_type}):")
            
            # Add slide plan details if available
            if "slide_plan" in slide_info:
                plan = slide_info["slide_plan"]
                context_parts.append(f"  Title: {plan.get('title', '')}")
                context_parts.append(f"  Key Message: {plan.get('key_message', '')}")
                
                # Add content blocks
                content_blocks = plan.get("content_blocks", [])
                if content_blocks:
                    context_parts.append(f"  Content ({len(content_blocks)} blocks):")
                    for j, block in enumerate(content_blocks):
                        block_type = block.get("type", "")
                        block_content = block.get("content", "")
                        context_parts.append(f"    {j+1}. [{block_type}] {block_content}")
                
                # Add existing visual elements
                existing_visuals = plan.get("visual_elements", [])
                if existing_visuals:
                    context_parts.append(f"  Existing Visuals ({len(existing_visuals)}):")
                    for j, visual in enumerate(existing_visuals):
                        visual_type = visual.get("type", "")
                        visual_desc = visual.get("description", "")
                        context_parts.append(f"    {j+1}. [{visual_type}] {visual_desc}")
                
                # Add chart data
                chart_data = plan.get("chart_data")
                if chart_data:
                    chart_type = chart_data.get("type", "")
                    context_parts.append(f"  Chart: {chart_type}")
        
        # Add transformation principles
        context_parts.append("\\nTransformation Principles:")
        context_parts.append("1. ALWAYS ask: 'Can this be visualized?'")
        context_parts.append("2. If YES → Create visual representation")
        context_parts.append("3. If NO → Limit to 6 text lines maximum")
        context_parts.append("4. Use flow diagrams for processes")
        context_parts.append("5. Use timelines for chronological content")
        context_parts.append("6. Use grids for comparisons")
        context_parts.append("7. Use diagrams for relationships")
        context_parts.append("8. Prioritize visual over text")
        
        # Add visual type specifications
        context_parts.append("\\nVisual Type Specifications:")
        context_parts.append("- flow: Sequential steps with arrows, decision points")
        context_parts.append("- timeline: Horizontal/vertical timeline with milestones")
        context_parts.append("- grid: Structured comparison table with rows/columns")
        context_parts.append("- diagram: Conceptual relationships, hierarchies")
        context_parts.append("- infographic: Data visualization, metrics display")
        
        return "\\n".join(context_parts)
    
    def _transform_slides_with_gemini(self, transformation_context: str, iteration: int) -> List[Dict[str, Any]]:
        """Transform slides using Gemini."""
        iteration_note = ""
        if iteration > 1:
            iteration_note = f"This is iteration {iteration}. Please improve upon previous attempts based on any feedback provided."
        
        prompt = f"""Analyze the slides below and transform text-heavy content into compelling visual elements.
        {iteration_note}
        
        {transformation_context}
        
        For each slide, provide:
        1. slide_number: The slide number
        2. visual_elements: Array of visual elements with:
           - type: flow, timeline, grid, diagram, infographic
           - layout: positioning and structure details
           - content: array of content items with positions
           - styling: visual styling recommendations
        3. text_content: Any remaining text (max 6 lines total)
        4. transformation_reasoning: Why this visual approach was chosen
        
        CRITICAL: Each slide should have visual elements unless it's truly text-only.
        Avoid paragraphs. Use structured layouts.
        
        Respond with JSON array of transformed slides."""
        
        output_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slide_number": {"type": "number"},
                    "visual_elements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "layout": {"type": "object"},
                                "content": {"type": "array"},
                                "styling": {"type": "object"}
                            }
                        }
                    },
                    "text_content": {"type": "string"},
                    "transformation_reasoning": {"type": "string"}
                },
                "required": ["slide_number", "visual_elements", "text_content", "transformation_reasoning"]
            }
        }
        
        try:
            response = self.call_gemini(prompt, output_schema)
            if isinstance(response, list):
                return response
        except Exception as e:
            self.logger.error(f"Error calling Gemini for visual transformation: {str(e)}")
        
        # Fallback: create basic visual transformations
        return self._create_fallback_transformations(transformation_context)
    
    def _create_fallback_transformations(self, transformation_context: str) -> List[Dict[str, Any]]:
        """Create fallback visual transformations if Gemini fails."""
        # Extract slide count from context
        import re
        slide_matches = re.findall(r'Slide (\d+)', transformation_context)
        slide_numbers = [int(match) for match in slide_matches]
        unique_slides = sorted(set(slide_numbers))
        
        transformations = []
        
        for slide_num in unique_slides:
            # Determine slide type from context
            slide_type_match = re.search(f'Slide {slide_num} \\(([^)]+)\\)', transformation_context)
            slide_type = slide_type_match.group(1) if slide_type_match else "section"
            
            # Create appropriate visual based on slide type
            visual_elements = []
            text_content = ""
            reasoning = f"Fallback transformation for {slide_type} slide"
            
            if slide_type == "process":
                visual_elements = [{
                    "type": "flow",
                    "layout": {
                        "direction": "horizontal",
                        "spacing": "even"
                    },
                    "content": [
                        {"text": "Step 1", "position": "left"},
                        {"text": "Step 2", "position": "center"},
                        {"text": "Step 3", "position": "right"}
                    ],
                    "styling": {
                        "arrows": True,
                        "boxes": True,
                        "colors": ["blue", "green", "orange"]
                    }
                }]
                text_content = "Process flow with three main steps"
            elif slide_type == "data":
                visual_elements = [{
                    "type": "infographic",
                    "layout": {
                        "style": "metric_cards"
                    },
                    "content": [
                        {"metric": "Key Metric 1", "value": "100", "position": "top-left"},
                        {"metric": "Key Metric 2", "value": "75%", "position": "top-right"},
                        {"metric": "Key Metric 3", "value": "$50K", "position": "bottom"}
                    ],
                    "styling": {
                        "card_style": "modern",
                        "colors": ["primary", "secondary", "accent"]
                    }
                }]
                text_content = "Key performance metrics dashboard"
            elif slide_type == "comparison":
                visual_elements = [{
                    "type": "grid",
                    "layout": {
                        "rows": 2,
                        "columns": 2,
                        "headers": True
                    },
                    "content": [
                        {"text": "Feature A", "position": "header-1"},
                        {"text": "Feature B", "position": "header-2"},
                        {"text": "Item 1", "position": "row1-col1"},
                        {"text": "Item 2", "position": "row1-col2"},
                        {"text": "Item 3", "position": "row2-col1"},
                        {"text": "Item 4", "position": "row2-col2"}
                    ],
                    "styling": {
                        "grid_style": "clean",
                        "borders": True
                    }
                }]
                text_content = "Feature comparison matrix"
            else:
                # Default to simple layout
                visual_elements = [{
                    "type": "diagram",
                    "layout": {
                        "style": "centered"
                    },
                    "content": [
                        {"text": "Main Point", "position": "center"},
                        {"text": "Support 1", "position": "left"},
                        {"text": "Support 2", "position": "right"}
                    ],
                    "styling": {
                        "connections": True,
                        "hierarchy": True
                    }
                }]
                text_content = "Key concept with supporting points"
            
            transformations.append({
                "slide_number": slide_num,
                "visual_elements": visual_elements,
                "text_content": text_content,
                "transformation_reasoning": reasoning
            })
        
        return transformations
    
    def _validate_visual_transformations(self, transformed_slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate visual transformations."""
        validated = []
        
        for slide in transformed_slides:
            slide_num = slide.get("slide_number", 0)
            
            # Ensure required fields
            if not all(key in slide for key in ["slide_number", "visual_elements", "text_content", "transformation_reasoning"]):
                self.logger.warning(f"Slide {slide_num} missing required fields, using fallback")
                slide = self._create_minimal_transformation(slide_num)
            
            # Validate visual elements
            visual_elements = slide.get("visual_elements", [])
            if not visual_elements:
                self.logger.warning(f"Slide {slide_num} has no visual elements")
                # Add basic visual element
                slide["visual_elements"] = [{
                    "type": "diagram",
                    "layout": {"style": "basic"},
                    "content": [{"text": slide.get("text_content", "Content"), "position": "center"}],
                    "styling": {"simple": True}
                }]
            
            # Check text content length
            text_content = slide.get("text_content", "")
            text_lines = len(text_content.split('\\n'))
            if text_lines > 6:
                self.logger.warning(f"Slide {slide_num} has too much text ({text_lines} lines), truncating")
                lines = text_content.split('\\n')
                slide["text_content"] = '\\n'.join(lines[:6])
            
            validated.append(slide)
        
        return validated
    
    def _create_minimal_transformation(self, slide_number: int) -> Dict[str, Any]:
        """Create a minimal valid visual transformation."""
        return {
            "slide_number": slide_number,
            "visual_elements": [{
                "type": "diagram",
                "layout": {"style": "simple"},
                "content": [{"text": f"Content for slide {slide_number}", "position": "center"}],
                "styling": {"minimal": True}
            }],
            "text_content": f"Slide {slide_number} content",
            "transformation_reasoning": "Minimal fallback transformation"
        }
    
    def _optimize_visual_impact(self, validated_transformations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize visual impact of transformations."""
        optimized = []
        
        for slide in validated_transformations:
            optimized_slide = slide.copy()
            visual_elements = slide.get("visual_elements", [])
            
            # Enhance visual elements
            enhanced_visuals = []
            for visual in visual_elements:
                enhanced_visual = self._enhance_visual_element(visual)
                enhanced_visuals.append(enhanced_visual)
            
            optimized_slide["visual_elements"] = enhanced_visuals
            optimized.append(optimized_slide)
        
        return optimized
    
    def _enhance_visual_element(self, visual: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a visual element with better styling and layout."""
        enhanced = visual.copy()
        
        visual_type = visual.get("type", "")
        layout = visual.get("layout", {})
        styling = visual.get("styling", {})
        
        # Add default styling based on type
        if visual_type == "flow":
            styling.setdefault("arrows", True)
            styling.setdefault("boxes", True)
            styling.setdefault("colors", ["#1f77b4", "#ff7f0e", "#2ca02c"])
            layout.setdefault("direction", "horizontal")
            layout.setdefault("spacing", "even")
        elif visual_type == "timeline":
            styling.setdefault("milestones", True)
            styling.setdefault("connections", True)
            styling.setdefault("colors", ["#d62728", "#ff7f0e", "#2ca02c"])
            layout.setdefault("orientation", "horizontal")
        elif visual_type == "grid":
            styling.setdefault("borders", True)
            styling.setdefault("headers", True)
            styling.setdefault("alternating_rows", False)
            layout.setdefault("responsive", True)
        elif visual_type == "diagram":
            styling.setdefault("connections", True)
            styling.setdefault("hierarchy", False)
            styling.setdefault("colors", ["#1f77b4", "#ff7f0e"])
            layout.setdefault("center_alignment", True)
        elif visual_type == "infographic":
            styling.setdefault("icons", True)
            styling.setdefault("data_labels", True)
            styling.setdefault("colors", ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])
        
        enhanced["layout"] = layout
        enhanced["styling"] = styling
        
        return enhanced
    
    def _create_transformation_summary(self, optimized_visuals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of visual transformations."""
        total_slides = len(optimized_visuals)
        visual_types_count = {}
        text_heavy_count = 0
        
        for slide in optimized_visuals:
            visual_elements = slide.get("visual_elements", [])
            text_content = slide.get("text_content", "")
            
            # Count visual types
            for visual in visual_elements:
                visual_type = visual.get("type", "unknown")
                visual_types_count[visual_type] = visual_types_count.get(visual_type, 0) + 1
            
            # Check text heaviness
            if len(text_content.split('\\n')) > 4:
                text_heavy_count += 1
        
        return {
            "total_slides_transformed": total_slides,
            "visual_types_distribution": visual_types_count,
            "slides_with_visuals": len([s for s in optimized_visuals if s.get("visual_elements")]),
            "text_heavy_slides": text_heavy_count,
            "transformation_success_rate": round((total_slides - text_heavy_count) / total_slides * 100, 1) if total_slides > 0 else 0
        }
    
    def _has_visual_type(self, slide: Dict[str, Any], visual_type: str) -> bool:
        """Check if slide has a specific visual type."""
        visual_elements = slide.get("visual_elements", [])
        return any(v.get("type") == visual_type for v in visual_elements)
    
    def _identify_text_heavy_slides(self, optimized_visuals: List[Dict[str, Any]]) -> List[int]:
        """Identify slides that are still too text-heavy."""
        text_heavy_slides = []
        
        for slide in optimized_visuals:
            slide_num = slide.get("slide_number", 0)
            text_content = slide.get("text_content", "")
            
            # Consider text-heavy if more than 4 lines or more than 200 characters
            if len(text_content.split('\\n')) > 4 or len(text_content) > 200:
                text_heavy_slides.append(slide_num)
        
        return text_heavy_slides
    
    def _calculate_visual_variety(self, optimized_visuals: List[Dict[str, Any]]) -> float:
        """Calculate visual variety score."""
        all_visual_types = set()
        total_visuals = 0
        
        for slide in optimized_visuals:
            visual_elements = slide.get("visual_elements", [])
            for visual in visual_elements:
                visual_type = visual.get("type", "unknown")
                all_visual_types.add(visual_type)
                total_visuals += 1
        
        if total_visuals == 0:
            return 0.0
        
        # Variety score based on number of unique types vs total visuals
        variety_score = len(all_visual_types) / total_visuals
        return round(variety_score, 2)
    
    def _get_visual_types_used(self, optimized_visuals: List[Dict[str, Any]]) -> List[str]:
        """Get list of visual types used."""
        visual_types = set()
        
        for slide in optimized_visuals:
            visual_elements = slide.get("visual_elements", [])
            for visual in visual_elements:
                visual_types.add(visual.get("type", "unknown"))
        
        return list(visual_types)
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate visual transformation output."""
        if not output:
            return False
        
        required_keys = ["visual_elements", "transformation_summary", "transformation_metadata"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in visual transformation output: {key}")
                return False
        
        # Validate visual elements
        visual_elements = output.get("visual_elements", [])
        if not isinstance(visual_elements, list):
            self.logger.error("visual_elements is not a list")
            return False
        
        # Validate each slide transformation
        for i, slide in enumerate(visual_elements):
            if not isinstance(slide, dict):
                self.logger.error(f"Slide transformation {i} is not a dictionary")
                return False
            
            required_slide_keys = ["slide_number", "visual_elements", "text_content", "transformation_reasoning"]
            for key in required_slide_keys:
                if key not in slide:
                    self.logger.error(f"Slide transformation {i} missing required key: {key}")
                    return False
        
        return True
