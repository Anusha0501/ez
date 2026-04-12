"""
Storyline Agent - Uses Gemini to create presentation narrative and structure.
"""

import json
import logging
from typing import Dict, Any, List

from core.agent import GeminiAgent
from core.models import Storyline


class StorylineAgent(GeminiAgent):
    """Agent responsible for creating the presentation storyline and narrative flow."""
    
    def __init__(self, gemini_client):
        system_prompt = """You are an expert presentation strategist and storyteller. 
        Your task is to transform analyzed content into a compelling presentation narrative 
        that follows consulting best practices.
        
        Key principles:
        1. Start with a strong title and agenda
        2. Include an executive summary
        3. Organize content into logical sections
        4. End with conclusions and recommendations
        5. Target 10-15 slides total
        6. Ensure each section supports the main message
        7. Create a logical flow that builds understanding
        
        Always respond in valid JSON format with the specified schema."""
        
        super().__init__("storyline_agent", gemini_client, system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a presentation storyline from analyzed content."""
        try:
            self.log_reasoning("start", "Starting storyline creation")
            
            parsed_data = input_data.get("parsed_data", {})
            insights = input_data.get("insights", {})
            executive_summary = insights.get("executive_summary", {})
            themes = insights.get("themes", [])
            
            if not parsed_data:
                raise ValueError("No parsed data provided")
            
            # Prepare content for storyline creation
            content_context = self._prepare_content_context(parsed_data, insights)
            
            self.log_reasoning("analyze_structure", "Analyzing content for storyline structure", {
                "sections_count": len(parsed_data.get("sections", [])),
                "insights_count": len(insights.get("insights", [])),
                "themes_count": len(themes)
            })
            
            # Determine optimal slide count
            self.log_reasoning("determine_slide_count", "Determining optimal slide count")
            slide_count = self._determine_slide_count(content_context)
            
            # Create narrative flow
            self.log_reasoning("create_narrative", "Creating presentation narrative")
            narrative_flow = self._create_narrative_flow(content_context, slide_count)
            
            # Define content distribution
            self.log_reasoning("distribute_content", "Distributing content across slides")
            content_distribution = self._distribute_content(slide_count, content_context)
            
            # Create detailed structure
            self.log_reasoning("create_structure", "Creating detailed slide structure")
            structure = self._create_detailed_structure(narrative_flow, content_distribution, content_context)
            
            # Extract key themes for emphasis
            self.log_reasoning("extract_key_themes", "Extracting key themes for emphasis")
            key_themes = self._extract_key_themes(themes, executive_summary)
            
            output = {
                "narrative_flow": narrative_flow,
                "slide_count": slide_count,
                "content_distribution": content_distribution,
                "key_themes": key_themes,
                "structure": structure,
                "storyline_metadata": {
                    "main_message": executive_summary.get("main_message", ""),
                    "presentation_type": self._determine_presentation_type(content_context),
                    "complexity_level": self._assess_complexity(content_context),
                    "target_audience": self._infer_target_audience(content_context)
                }
            }
            
            self.log_reasoning("complete", "Successfully created storyline", {
                "slide_count": slide_count,
                "narrative_steps": len(narrative_flow),
                "key_themes": len(key_themes)
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in storyline agent: {str(e)}")
            # Return fallback result instead of crashing
            fallback_result = self._create_fallback_storyline({"parsed_data": parsed_data, "insights": insights})
            self.log_reasoning("fallback", "Using fallback storyline due to agent failure", {
                "error": str(e),
                "fallback_applied": True
            })
            return fallback_result
    
    def _prepare_content_context(self, parsed_data: Dict, insights: Dict) -> str:
        """Prepare a comprehensive context for storyline creation."""
        context_parts = []
        
        # Add title and main message
        title = parsed_data.get("title", "Untitled Presentation")
        main_message = insights.get("executive_summary", {}).get("main_message", "")
        
        context_parts.append(f"Title: {title}")
        if main_message:
            context_parts.append(f"Main Message: {main_message}")
        
        # Add sections overview
        sections = parsed_data.get("sections", [])
        if sections:
            context_parts.append("\\nDocument Sections:")
            for i, section in enumerate(sections[:8]):  # Limit to first 8 sections
                section_title = section.get("title", f"Section {i+1}")
                context_parts.append(f"{i+1}. {section_title}")
        
        # Add key insights
        insights_list = insights.get("insights", [])
        if insights_list:
            context_parts.append("\\nKey Insights:")
            for i, insight in enumerate(insights_list[:5]):  # Limit to first 5 insights
                insight_text = insight.get("text", "")
                context_parts.append(f"• {insight_text}")
        
        # Add themes
        themes = insights.get("themes", [])
        if themes:
            context_parts.append("\\nMajor Themes:")
            for theme in themes[:4]:  # Limit to first 4 themes
                theme_name = theme.get("name", "")
                relevance = theme.get("relevance", 0)
                context_parts.append(f"• {theme_name} (relevance: {relevance})")
        
        # Add recommendations
        recommendations = insights.get("executive_summary", {}).get("recommendations", [])
        if recommendations:
            context_parts.append("\\nKey Recommendations:")
            for rec in recommendations[:3]:  # Limit to first 3 recommendations
                context_parts.append(f"• {rec}")
        
        # Add metrics overview
        metrics = insights.get("metrics", [])
        if metrics:
            context_parts.append(f"\\nKey Metrics Available: {len(metrics)} metrics")
            for metric in metrics[:3]:  # Limit to first 3 metrics
                metric_name = metric.get("name", "")
                metric_value = metric.get("value", "")
                context_parts.append(f"• {metric_name}: {metric_value}")
        
        return "\\n".join(context_parts)
    
    def _determine_slide_count(self, content_context: str) -> int:
        """Determine the optimal number of slides based on content complexity."""
        prompt = f"""Based on the content context below, determine the optimal number of slides for a consulting presentation.
        The target range is 10-15 slides.
        
        Content Context:
        {content_context}
        
        Consider:
        - Content complexity and depth
        - Number of main sections
        - Number of key insights
        - Need for introduction, agenda, and conclusion
        
        Respond with just the number (e.g., 12)."""
        
        try:
            response = self.call_gemini(prompt)
            # Extract number from response
            import re
            numbers = re.findall(r'\\b(10|11|12|13|14|15)\\b', response)
            if numbers:
                return int(numbers[0])
        except:
            pass
        
        # Fallback logic based on content analysis
        context_lines = len(content_context.split('\\n'))
        if context_lines < 20:
            return 10
        elif context_lines < 40:
            return 12
        else:
            return 14
    
    def _create_narrative_flow(self, content_context: str, slide_count: int) -> List[str]:
        """Create the narrative flow for the presentation."""
        prompt = f"""Create a narrative flow for a {slide_count}-slide presentation based on the content context.
        The flow should follow consulting presentation best practices:
        1. Title slide
        2. Agenda
        3. Executive Summary
        4-?. Main content sections (logical progression)
        ?. Conclusions
        ?. Recommendations/Next Steps
        
        Content Context:
        {content_context}
        
        Provide a list of {slide_count} narrative steps, each describing what that slide should accomplish.
        Make the flow logical and compelling.
        
        Respond with JSON array of strings."""
        
        output_schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        
        try:
            response = self.call_gemini(prompt, output_schema)
            if isinstance(response, list) and len(response) >= slide_count:
                return response[:slide_count]
        except:
            pass
        
        # Fallback narrative structure
        fallback_flow = [
            "Title slide with compelling headline",
            "Agenda outlining presentation structure",
            "Executive summary with key findings",
            "Current situation analysis",
            "Key challenges and opportunities",
            "Data-driven insights",
            "Strategic implications",
            "Proposed solutions",
            "Implementation roadmap",
            "Expected outcomes and benefits",
            "Risk assessment and mitigation",
            "Conclusions and next steps"
        ]
        
        return fallback_flow[:slide_count]
    
    def _distribute_content(self, slide_count: int, content_context: str) -> Dict[str, int]:
        """Determine how many slides to allocate to each content type."""
        prompt = f"""For a {slide_count}-slide presentation, determine how many slides to allocate to each section type.
        
        Content Context:
        {content_context}
        
        Allocate slides among these categories:
        - introduction: Title, agenda
        - summary: Executive summary
        - analysis: Data, insights, findings
        - strategy: Strategic implications, solutions
        - implementation: Roadmap, actions
        - conclusion: Conclusions, recommendations
        
        Ensure the total equals {slide_count}. Provide realistic distribution.
        
        Respond with JSON object with numeric values."""
        
        output_schema = {
            "type": "object",
            "properties": {
                "introduction": {"type": "number"},
                "summary": {"type": "number"},
                "analysis": {"type": "number"},
                "strategy": {"type": "number"},
                "implementation": {"type": "number"},
                "conclusion": {"type": "number"}
            },
            "required": ["introduction", "summary", "analysis", "strategy", "implementation", "conclusion"]
        }
        
        try:
            response = self.call_gemini(prompt, output_schema)
            if isinstance(response, dict):
                # Adjust to ensure total equals slide_count
                total = sum(response.values())
                if total != slide_count:
                    # Scale proportionally
                    scale_factor = slide_count / total
                    for key in response:
                        response[key] = max(1, round(response[key] * scale_factor))
                    
                    # Adjust for rounding errors
                    current_total = sum(response.values())
                    diff = slide_count - current_total
                    if diff != 0:
                        # Add or remove from the largest category
                        largest_category = max(response.keys(), key=lambda k: response[k])
                        response[largest_category] += diff
                
                return response
        except:
            pass
        
        # Fallback distribution handled by main _create_fallback_storyline method
    
    def _create_detailed_structure(self, narrative_flow: List[str], content_distribution: Dict[str, int], content_context: str) -> List[Dict[str, Any]]:
        """Create detailed slide structure based on narrative flow and distribution."""
        structure = []
        current_slide = 1
        
        # Map distribution to narrative flow
        for i, step in enumerate(narrative_flow):
            slide_type = self._classify_slide_type(step, i, len(narrative_flow))
            
            structure.append({
                "slide_number": current_slide,
                "title": self._generate_slide_title(step, slide_type),
                "slide_type": slide_type,
                "narrative_purpose": step,
                "content_focus": self._determine_content_focus(slide_type, content_context),
                "estimated_complexity": self._estimate_slide_complexity(step, content_context)
            })
            
            current_slide += 1
        
        return structure
    
    def _classify_slide_type(self, step: str, index: int, total_slides: int) -> str:
        """Classify the type of slide based on its purpose."""
        step_lower = step.lower()
        
        if index == 0:
            return "title"
        elif "agenda" in step_lower:
            return "section"
        elif "executive summary" in step_lower or "summary" in step_lower:
            return "summary"
        elif "conclusion" in step_lower or "recommendation" in step_lower:
            return "summary"
        elif "data" in step_lower or "analysis" in step_lower or "insight" in step_lower:
            return "data"
        elif "comparison" in step_lower or "vs" in step_lower:
            return "comparison"
        elif "process" in step_lower or "roadmap" in step_lower or "flow" in step_lower:
            return "process"
        else:
            return "section"
    
    def _generate_slide_title(self, step: str, slide_type: str) -> str:
        """Generate an appropriate title for the slide."""
        step_lower = step.lower()
        
        if slide_type == "title":
            return "Title"
        elif "agenda" in step_lower:
            return "Agenda"
        elif "executive summary" in step_lower:
            return "Executive Summary"
        elif "conclusion" in step_lower:
            return "Conclusions"
        elif "recommendation" in step_lower:
            return "Recommendations"
        else:
            # Extract key phrase from step
            words = step.split()
            if len(words) <= 5:
                return step.title()
            else:
                return " ".join(words[:5]).title()
    
    def _determine_content_focus(self, slide_type: str, content_context: str) -> str:
        """Determine the main content focus for a slide type."""
        focus_map = {
            "title": "overview",
            "section": "transition",
            "summary": "key_points",
            "data": "analysis",
            "comparison": "contrast",
            "process": "sequence"
        }
        
        return focus_map.get(slide_type, "general")
    
    def _estimate_slide_complexity(self, step: str, content_context: str) -> str:
        """Estimate the complexity level of a slide."""
        step_lower = step.lower()
        
        if any(word in step_lower for word in ["data", "analysis", "detailed"]):
            return "high"
        elif any(word in step_lower for word in ["summary", "overview", "introduction"]):
            return "low"
        else:
            return "medium"
    
    def _extract_key_themes(self, themes: List, executive_summary: Dict) -> List[str]:
        """Extract the most important themes for emphasis."""
        if not themes:
            return []
        
        # Sort themes by relevance
        sorted_themes = sorted(themes, key=lambda x: x.get("relevance", 0), reverse=True)
        
        # Extract top themes
        key_themes = [theme.get("name", "") for theme in sorted_themes[:4]]
        
        # Add main message if available
        main_message = executive_summary.get("main_message", "")
        if main_message and len(main_message.split()) <= 5:
            key_themes.insert(0, main_message)
        
        return [theme for theme in key_themes if theme][:5]  # Limit to 5 themes
    
    def _determine_presentation_type(self, content_context: str) -> str:
        """Determine the type of presentation."""
        context_lower = content_context.lower()
        
        if any(word in context_lower for word in ["financial", "budget", "revenue", "cost"]):
            return "financial"
        elif any(word in context_lower for word in ["strategy", "strategic", "plan"]):
            return "strategic"
        elif any(word in context_lower for word in ["data", "analysis", "research"]):
            return "analytical"
        elif any(word in context_lower for word in ["project", "implementation", "roadmap"]):
            return "project"
        else:
            return "general"
    
    def _assess_complexity(self, content_context: str) -> str:
        """Assess the overall complexity of the content."""
        word_count = len(content_context.split())
        
        # Count complex indicators
        complex_indicators = ["analysis", "strategic", "implementation", "detailed", "comprehensive"]
        complex_count = sum(1 for indicator in complex_indicators if indicator in content_context.lower())
        
        if word_count > 300 or complex_count > 3:
            return "high"
        elif word_count > 150 or complex_count > 1:
            return "medium"
        else:
            return "low"
    
    def _infer_target_audience(self, content_context: str) -> str:
        """Infer the target audience from content."""
        context_lower = content_context.lower()
        
        if any(word in context_lower for word in ["executive", "board", "leadership"]):
            return "executives"
        elif any(word in context_lower for word in ["technical", "engineering", "development"]):
            return "technical"
        elif any(word in context_lower for word in ["financial", "investor", "shareholder"]):
            return "financial"
        elif any(word in context_lower for word in ["customer", "client", "user"]):
            return "customers"
        else:
            return "general"
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the storyline output."""
        if not output:
            return False
        
        required_keys = ["narrative_flow", "slide_count", "content_distribution", "key_themes", "structure"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in storyline output: {key}")
                return False
        
        # Validate slide count
        slide_count = output.get("slide_count", 0)
        fallback_used = output.get("storyline_metadata", {}).get("fallback_used", False)
        min_slides = 4 if fallback_used else 10
        if not isinstance(slide_count, int) or slide_count < min_slides or slide_count > 15:
            self.logger.error(f"Invalid slide count: {slide_count}")
            return False
        
        # Validate narrative flow length
        narrative_flow = output.get("narrative_flow", [])
        if not isinstance(narrative_flow, list) or len(narrative_flow) != slide_count:
            self.logger.error("Narrative flow length doesn't match slide count")
            return False
        
        return True
    
    def _create_fallback_storyline(self, data):
        """Create fallback storyline when Gemini fails."""
        self.logger.warning("Gemini failed → using fallback")
        if not isinstance(data, dict):
            data = {}
        fallback_slides = [
            {"title": "Overview", "content": ["Summary of document"]},
            {"title": "Key Insights", "content": ["Insight 1", "Insight 2"]},
            {"title": "Analysis", "content": ["Analysis point"]},
            {"title": "Conclusion", "content": ["Final takeaway"]},
        ]

        return {
            "narrative_flow": [s["title"] for s in fallback_slides],
            "slide_count": len(fallback_slides),
            "content_distribution": {
                "introduction": 1,
                "summary": 1,
                "analysis": 1,
                "strategy": 0,
                "implementation": 0,
                "conclusion": 1
            },
            "key_themes": [s["title"] for s in fallback_slides],
            "structure": [
                {
                    "slide_number": i + 1,
                    "title": s["title"],
                    "narrative_purpose": s["content"][0],
                    "slide_type": "content"
                }
                for i, s in enumerate(fallback_slides)
            ],
            "fallback_slides": fallback_slides,
            "storyline_metadata": {"fallback_used": True}
        }
