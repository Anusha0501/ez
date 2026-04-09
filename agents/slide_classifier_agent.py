"""
Slide Type Classifier Agent - Uses Gemini to classify slides into appropriate types.
"""

import json
import logging
from typing import Dict, Any, List

from core.agent import GeminiAgent
from core.models import SlideType


class SlideClassifierAgent(GeminiAgent):
    """Agent responsible for classifying slides into appropriate types."""
    
    def __init__(self, gemini_client):
        system_prompt = """You are an expert presentation designer specializing in slide classification.
        Your task is to analyze slide plans and classify each slide into the most appropriate type.
        
        Slide Types:
        - title: Title slide with main heading and subtitle
        - section: Section divider or transition slide
        - data: Data-heavy slide with charts, graphs, or tables
        - comparison: Slide comparing multiple items, options, or scenarios
        - process: Process flow, timeline, or sequential steps
        - summary: Summary, conclusion, or recommendation slide
        
        Classification Criteria:
        1. Content type and purpose
        2. Visual elements required
        3. Data presence
        4. Narrative function
        5. Audience interaction needs
        
        Always respond in valid JSON format with the specified schema."""
        
        super().__init__("slide_classifier_agent", gemini_client, system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify slides into appropriate types."""
        try:
            self.log_reasoning("start", "Starting slide classification")
            
            slide_plans = input_data.get("slide_plans", [])
            
            if not slide_plans:
                raise ValueError("No slide plans provided")
            
            # Prepare context for classification
            classification_context = self._prepare_classification_context(slide_plans)
            
            self.log_reasoning("analyze_slides", "Analyzing slides for classification", {
                "total_slides": len(slide_plans),
                "slides_with_charts": sum(1 for plan in slide_plans if plan.get("chart_data")),
                "slides_with_visuals": sum(1 for plan in slide_plans if plan.get("visual_elements"))
            })
            
            # Classify slides using Gemini
            self.log_reasoning("classify_slides", "Classifying slides with Gemini")
            classified_slides = self._classify_slides_with_gemini(classification_context)
            
            # Validate and adjust classifications
            self.log_reasoning("validate_classifications", "Validating and adjusting classifications")
            validated_classifications = self._validate_and_adjust_classifications(classified_slides, slide_plans)
            
            # Create classification summary
            self.log_reasoning("create_summary", "Creating classification summary")
            classification_summary = self._create_classification_summary(validated_classifications)
            
            # Ensure logical flow
            self.log_reasoning("ensure_flow", "Ensuring logical flow between slide types")
            optimized_classifications = self._ensure_logical_flow(validated_classifications)
            
            output = {
                "classified_slides": optimized_classifications,
                "classification_summary": classification_summary,
                "classification_metadata": {
                    "total_slides": len(optimized_classifications),
                    "type_distribution": self._get_type_distribution(optimized_classifications),
                    "classification_confidence": self._calculate_classification_confidence(optimized_classifications),
                    "flow_optimizations": self._get_flow_optimizations(validated_classifications, optimized_classifications)
                }
            }
            
            self.log_reasoning("complete", "Successfully classified slides", {
                "total_classified": len(optimized_classifications),
                "unique_types": len(set(slide.get("slide_type") for slide in optimized_classifications))
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in slide classifier agent: {str(e)}")
            raise
    
    def _prepare_classification_context(self, slide_plans: List[Dict[str, Any]]) -> str:
        """Prepare context for slide classification."""
        context_parts = []
        
        context_parts.append("Slide Plans for Classification:")
        
        for i, plan in enumerate(slide_plans):
            context_parts.append(f"\\nSlide {i+1}:")
            context_parts.append(f"  Title: {plan.get('title', '')}")
            context_parts.append(f"  Key Message: {plan.get('key_message', '')}")
            
            # Add content blocks summary
            content_blocks = plan.get("content_blocks", [])
            if content_blocks:
                context_parts.append(f"  Content ({len(content_blocks)} blocks):")
                for j, block in enumerate(content_blocks[:3]):  # Limit to first 3 blocks
                    block_type = block.get("type", "")
                    block_content = block.get("content", "")[:50]
                    context_parts.append(f"    {j+1}. [{block_type}] {block_content}...")
            
            # Add visual elements summary
            visual_elements = plan.get("visual_elements", [])
            if visual_elements:
                context_parts.append(f"  Visual Elements ({len(visual_elements)}):")
                for j, visual in enumerate(visual_elements[:2]):  # Limit to first 2 elements
                    visual_type = visual.get("type", "")
                    visual_desc = visual.get("description", "")[:30]
                    context_parts.append(f"    {j+1}. [{visual_type}] {visual_desc}...")
            
            # Add chart data info
            chart_data = plan.get("chart_data")
            if chart_data:
                chart_type = chart_data.get("type", "")
                context_parts.append(f"  Chart: {chart_type}")
            
            # Add position in presentation
            position_note = ""
            if i == 0:
                position_note = " (First slide - likely title)"
            elif i == len(slide_plans) - 1:
                position_note = " (Last slide - likely conclusion)"
            elif i == 1:
                position_note = " (Second slide - likely agenda)"
            
            if position_note:
                context_parts.append(f"  Position Note: {position_note}")
        
        # Add classification guidelines
        context_parts.append("\\nClassification Guidelines:")
        context_parts.append("- title: First slide or main section headers")
        context_parts.append("- section: Transition/agenda/divider slides")
        context_parts.append("- data: Slides with charts, tables, or numerical data")
        context_parts.append("- comparison: Slides comparing multiple items")
        context_parts.append("- process: Slides showing steps, flows, or timelines")
        context_parts.append("- summary: Conclusion, recommendation, or summary slides")
        
        return "\\n".join(context_parts)
    
    def _classify_slides_with_gemini(self, classification_context: str) -> List[Dict[str, Any]]:
        """Classify slides using Gemini."""
        prompt = f"""Analyze the slide plans below and classify each slide into the most appropriate type.
        For each slide, provide:
        1. slide_number: The slide number (1-based)
        2. slide_type: One of: title, section, data, comparison, process, summary
        3. confidence: Confidence score from 0.0 to 1.0
        4. reasoning: Brief explanation of why this type was chosen
        
        {classification_context}
        
        Consider the slide's position in the presentation, content type, and visual elements.
        Ensure logical flow between slide types.
        
        Respond with JSON array of classifications."""
        
        output_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slide_number": {"type": "number"},
                    "slide_type": {"type": "string"},
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"}
                },
                "required": ["slide_number", "slide_type", "confidence", "reasoning"]
            }
        }
        
        try:
            response = self.call_gemini(prompt, output_schema)
            if isinstance(response, list):
                return response
        except Exception as e:
            self.logger.error(f"Error calling Gemini for slide classification: {str(e)}")
        
        # Fallback: create basic classifications
        return self._create_fallback_classifications(classification_context)
    
    def _create_fallback_classifications(self, classification_context: str) -> List[Dict[str, Any]]:
        """Create fallback classifications if Gemini fails."""
        # Extract slide count from context
        import re
        slide_matches = re.findall(r'Slide (\d+):', classification_context)
        slide_count = len(slide_matches)
        
        if slide_count == 0:
            slide_count = 12  # Default
        
        classifications = []
        
        for i in range(slide_count):
            slide_num = i + 1
            slide_type = "section"  # Default
            confidence = 0.5
            reasoning = "Fallback classification"
            
            # Basic logic for classification
            if slide_num == 1:
                slide_type = "title"
                confidence = 0.9
                reasoning = "First slide is typically a title slide"
            elif slide_num == 2:
                slide_type = "section"
                confidence = 0.8
                reasoning = "Second slide is typically an agenda"
            elif slide_num >= slide_count - 2:
                slide_type = "summary"
                confidence = 0.7
                reasoning = "Last slides are typically conclusions/recommendations"
            
            classifications.append({
                "slide_number": slide_num,
                "slide_type": slide_type,
                "confidence": confidence,
                "reasoning": reasoning
            })
        
        return classifications
    
    def _validate_and_adjust_classifications(self, classifications: List[Dict[str, Any]], slide_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and adjust slide classifications."""
        validated = []
        
        for classification in classifications:
            slide_num = classification.get("slide_number", 0)
            
            # Get corresponding slide plan
            slide_plan = None
            if 1 <= slide_num <= len(slide_plans):
                slide_plan = slide_plans[slide_num - 1]
            
            # Validate slide type
            slide_type = classification.get("slide_type", "")
            if slide_type not in [t.value for t in SlideType]:
                # Adjust to valid type
                if slide_plan:
                    slide_type = self._infer_type_from_plan(slide_plan)
                else:
                    slide_type = "section"
                
                classification["slide_type"] = slide_type
                classification["reasoning"] += f" (Adjusted to {slide_type})"
            
            # Adjust based on slide content
            if slide_plan:
                adjusted_type = self._adjust_type_based_on_content(classification["slide_type"], slide_plan)
                if adjusted_type != classification["slide_type"]:
                    classification["slide_type"] = adjusted_type
                    classification["reasoning"] += f" (Content-based adjustment to {adjusted_type})"
            
            validated.append(classification)
        
        return validated
    
    def _infer_type_from_plan(self, slide_plan: Dict[str, Any]) -> str:
        """Infer slide type from slide plan."""
        title = slide_plan.get("title", "").lower()
        key_message = slide_plan.get("key_message", "").lower()
        chart_data = slide_plan.get("chart_data")
        visual_elements = slide_plan.get("visual_elements", [])
        
        # Check for indicators
        if any(word in title for word in ["title", "introduction", "overview"]):
            return "title"
        elif any(word in title for word in ["agenda", "outline", "structure"]):
            return "section"
        elif chart_data:
            return "data"
        elif any(word in title for word in ["conclusion", "summary", "recommendation"]):
            return "summary"
        elif any(word in title for word in ["process", "flow", "steps", "timeline"]):
            return "process"
        elif any(word in title for word in ["comparison", "versus", "vs", "analysis"]):
            return "comparison"
        else:
            return "section"
    
    def _adjust_type_based_on_content(self, current_type: str, slide_plan: Dict[str, Any]) -> str:
        """Adjust slide type based on slide content."""
        chart_data = slide_plan.get("chart_data")
        visual_elements = slide_plan.get("visual_elements", [])
        content_blocks = slide_plan.get("content_blocks", [])
        
        # Strong indicators for data slides
        if chart_data and current_type != "data":
            return "data"
        
        # Check for process indicators in visual elements
        for visual in visual_elements:
            visual_type = visual.get("type", "").lower()
            if any(word in visual_type for word in ["flow", "process", "timeline"]) and current_type != "process":
                return "process"
        
        # Check for comparison indicators
        title = slide_plan.get("title", "").lower()
        if any(word in title for word in ["comparison", "versus", "vs", "analysis"]) and current_type != "comparison":
            return "comparison"
        
        return current_type
    
    def _ensure_logical_flow(self, classifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure logical flow between slide types."""
        optimized = classifications.copy()
        
        # Ensure first slide is title
        if optimized and optimized[0].get("slide_type") != "title":
            optimized[0]["slide_type"] = "title"
            optimized[0]["reasoning"] += " (Flow optimization: first slide should be title)"
        
        # Ensure second slide is section (agenda)
        if len(optimized) > 1 and optimized[1].get("slide_type") not in ["section", "title"]:
            optimized[1]["slide_type"] = "section"
            optimized[1]["reasoning"] += " (Flow optimization: second slide should be agenda)"
        
        # Ensure last slides are summary
        if len(optimized) >= 2:
            # Last slide
            if optimized[-1].get("slide_type") not in ["summary", "title"]:
                optimized[-1]["slide_type"] = "summary"
                optimized[-1]["reasoning"] += " (Flow optimization: last slide should be summary)"
            
            # Second to last slide
            if optimized[-2].get("slide_type") not in ["summary", "data", "process"]:
                optimized[-2]["slide_type"] = "summary"
                optimized[-2]["reasoning"] += " (Flow optimization: penultimate slide should be summary)"
        
        return optimized
    
    def _create_classification_summary(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of slide classifications."""
        type_counts = {}
        confidence_scores = []
        
        for classification in classifications:
            slide_type = classification.get("slide_type", "")
            confidence = classification.get("confidence", 0)
            
            type_counts[slide_type] = type_counts.get(slide_type, 0) + 1
            confidence_scores.append(confidence)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            "type_counts": type_counts,
            "total_slides": len(classifications),
            "average_confidence": round(avg_confidence, 2),
            "high_confidence_slides": len([c for c in confidence_scores if c >= 0.8]),
            "low_confidence_slides": len([c for c in confidence_scores if c < 0.6])
        }
    
    def _get_type_distribution(self, classifications: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get the distribution of slide types as percentages."""
        total_slides = len(classifications)
        if total_slides == 0:
            return {}
        
        type_counts = {}
        for classification in classifications:
            slide_type = classification.get("slide_type", "")
            type_counts[slide_type] = type_counts.get(slide_type, 0) + 1
        
        return {
            slide_type: round((count / total_slides) * 100, 1)
            for slide_type, count in type_counts.items()
        }
    
    def _calculate_classification_confidence(self, classifications: List[Dict[str, Any]]) -> float:
        """Calculate overall classification confidence."""
        if not classifications:
            return 0.0
        
        confidences = [c.get("confidence", 0) for c in classifications]
        return round(sum(confidences) / len(confidences), 2)
    
    def _get_flow_optimizations(self, original: List[Dict[str, Any]], optimized: List[Dict[str, Any]]) -> List[str]:
        """Get list of flow optimizations made."""
        optimizations = []
        
        for i, (orig, opt) in enumerate(zip(original, optimized)):
            if orig.get("slide_type") != opt.get("slide_type"):
                optimizations.append(
                    f"Slide {i+1}: {orig.get('slide_type')} → {opt.get('slide_type')}"
                )
        
        return optimizations
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the classification output."""
        if not output:
            return False
        
        required_keys = ["classified_slides", "classification_summary", "classification_metadata"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in classification output: {key}")
                return False
        
        # Validate classified slides
        classified_slides = output.get("classified_slides", [])
        if not isinstance(classified_slides, list):
            self.logger.error("classified_slides is not a list")
            return False
        
        # Validate each classification
        valid_types = [t.value for t in SlideType]
        for i, classification in enumerate(classified_slides):
            if not isinstance(classification, dict):
                self.logger.error(f"Classification {i} is not a dictionary")
                return False
            
            slide_type = classification.get("slide_type", "")
            if slide_type not in valid_types:
                self.logger.error(f"Invalid slide type: {slide_type}")
                return False
        
        return True
