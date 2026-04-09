"""
Insight Extraction Agent - Uses Gemini to extract key insights, themes, and metrics.
"""

import json
import logging
from typing import Dict, Any, List

from ..core.agent import GeminiAgent
from ..core.models import Insight, ExecutiveSummary


class InsightAgent(GeminiAgent):
    """Agent responsible for extracting insights from parsed content."""
    
    def __init__(self, gemini_client):
        system_prompt = """You are an expert business analyst and insights extraction specialist. 
        Your task is to analyze structured markdown content and extract the most important insights, 
        themes, and metrics that would be valuable for a consulting-level presentation.
        
        Focus on:
        1. Key business insights and strategic implications
        2. Important metrics and KPIs
        3. Themes and patterns
        4. Actionable recommendations
        5. Executive summary points
        
        Always respond in valid JSON format with the specified schema."""
        
        super().__init__("insight_agent", gemini_client, system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from parsed markdown data."""
        try:
            self.log_reasoning("start", "Starting insight extraction")
            
            parsed_data = input_data.get("parsed_data", {})
            numeric_data = input_data.get("numeric_data", [])
            structure_analysis = input_data.get("structure_analysis", {})
            
            if not parsed_data:
                raise ValueError("No parsed data provided")
            
            # Prepare content for analysis
            content_summary = self._prepare_content_summary(parsed_data, numeric_data, structure_analysis)
            
            self.log_reasoning("analyze_content", "Analyzing content for insights", {
                "elements_count": len(parsed_data.get("elements", [])),
                "sections_count": len(parsed_data.get("sections", [])),
                "numeric_points": len(numeric_data)
            })
            
            # Extract key insights using Gemini
            insights = self._extract_insights(content_summary)
            
            # Generate executive summary
            self.log_reasoning("generate_summary", "Generating executive summary")
            executive_summary = self._generate_executive_summary(content_summary, insights)
            
            # Identify key themes
            self.log_reasoning("identify_themes", "Identifying key themes")
            themes = self._identify_themes(content_summary)
            
            # Extract important metrics
            self.log_reasoning("extract_metrics", "Extracting important metrics")
            metrics = self._extract_metrics(numeric_data, content_summary)
            
            output = {
                "insights": insights,
                "executive_summary": executive_summary,
                "themes": themes,
                "metrics": metrics,
                "analysis_metadata": {
                    "total_insights": len(insights),
                    "total_themes": len(themes),
                    "total_metrics": len(metrics),
                    "content_depth": self._assess_content_depth(content_summary)
                }
            }
            
            self.log_reasoning("complete", "Successfully extracted insights", {
                "insights_found": len(insights),
                "themes_found": len(themes),
                "metrics_found": len(metrics)
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in insight agent: {str(e)}")
            raise
    
    def _prepare_content_summary(self, parsed_data: Dict, numeric_data: List, structure_analysis: Dict) -> str:
        """Prepare a comprehensive summary of the content for analysis."""
        summary_parts = []
        
        # Add title if available
        title = parsed_data.get("title", "Untitled Document")
        summary_parts.append(f"Document Title: {title}")
        
        # Add section overview
        sections = parsed_data.get("sections", [])
        if sections:
            summary_parts.append("\\nSections:")
            for section in sections[:5]:  # Limit to first 5 sections
                summary_parts.append(f"- {section.get('title', 'Unknown Section')}")
        
        # Add key content from elements
        elements = parsed_data.get("elements", [])
        if elements:
            summary_parts.append("\\nKey Content:")
            
            # Extract headings
            headings = [e for e in elements if e.get("type") == "heading"]
            for heading in headings[:10]:  # Limit to first 10 headings
                summary_parts.append(f"• {heading.get('content', '')}")
            
            # Extract key paragraphs (first sentence only)
            paragraphs = [e for e in elements if e.get("type") == "paragraph"]
            for para in paragraphs[:3]:  # Limit to first 3 paragraphs
                content = para.get("content", "")
                first_sentence = content.split('.')[0] + '.' if '.' in content else content
                summary_parts.append(f"• {first_sentence}")
        
        # Add numeric data overview
        if numeric_data:
            summary_parts.append("\\nNumeric Data Points:")
            for data_point in numeric_data[:5]:  # Limit to first 5
                context = data_point.get("context", "")[:100]
                values = data_point.get("value", [])
                summary_parts.append(f"• {context} (Values: {', '.join(values[:3])})")
        
        # Add structure insights
        if structure_analysis:
            content_types = structure_analysis.get("content_types", {})
            summary_parts.append(f"\\nContent Types: {dict(list(content_types.items())[:5])}")
        
        return "\\n".join(summary_parts)
    
    def _extract_insights(self, content_summary: str) -> List[Dict[str, Any]]:
        """Extract key insights using Gemini."""
        prompt = f"""Analyze the following content and extract the 5-7 most important insights.
        Each insight should be strategic, actionable, and valuable for a business presentation.
        
        Content:
        {content_summary}
        
        For each insight, provide:
        - text: The insight statement (clear and concise)
        - importance: Score from 0.0 to 1.0 indicating business impact
        - category: Type of insight (e.g., "strategic", "operational", "financial", "market")
        - supporting_data: Brief reference to supporting data points
        
        Respond with JSON array of insights."""
        
        output_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "importance": {"type": "number"},
                    "category": {"type": "string"},
                    "supporting_data": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["text", "importance", "category"]
            }
        }
        
        response = self.call_gemini(prompt, output_schema)
        return response if isinstance(response, list) else []
    
    def _generate_executive_summary(self, content_summary: str, insights: List) -> Dict[str, Any]:
        """Generate an executive summary using Gemini."""
        insights_text = "\\n".join([f"- {insight.get('text', '')}" for insight in insights[:3]])
        
        prompt = f"""Based on the content and key insights below, generate an executive summary for a consulting presentation.
        
        Content Summary:
        {content_summary}
        
        Key Insights:
        {insights_text}
        
        Provide:
        - main_message: One sentence capturing the core message
        - key_insights: Top 3 insights (reusing from above)
        - recommendations: 3-4 actionable recommendations
        - metrics: 3-5 key metrics that should be highlighted
        
        Respond with JSON object."""
        
        output_schema = {
            "type": "object",
            "properties": {
                "main_message": {"type": "string"},
                "key_insights": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "metrics": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["main_message", "key_insights", "recommendations", "metrics"]
        }
        
        response = self.call_gemini(prompt, output_schema)
        return response if isinstance(response, dict) else {}
    
    def _identify_themes(self, content_summary: str) -> List[Dict[str, Any]]:
        """Identify key themes in the content."""
        prompt = f"""Analyze the content and identify 4-6 major themes or topics.
        Themes should represent the main subject areas or recurring concepts.
        
        Content:
        {content_summary}
        
        For each theme, provide:
        - name: Theme name (short, descriptive)
        - description: Brief description of the theme
        - relevance: Score from 0.0 to 1.0 indicating importance
        
        Respond with JSON array of themes."""
        
        output_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "relevance": {"type": "number"}
                },
                "required": ["name", "description", "relevance"]
            }
        }
        
        response = self.call_gemini(prompt, output_schema)
        return response if isinstance(response, list) else []
    
    def _extract_metrics(self, numeric_data: List, content_summary: str) -> List[Dict[str, Any]]:
        """Extract and prioritize important metrics."""
        # First, extract metrics from numeric data
        metrics_from_data = []
        for data_point in numeric_data[:10]:  # Limit to first 10
            values = data_point.get("value", [])
            context = data_point.get("context", "")
            
            for value in values[:3]:  # Limit to first 3 values per data point
                try:
                    # Clean the value
                    clean_value = value.replace('%', '').replace(',', '')
                    if clean_value.replace('.', '').replace('-', '').isdigit():
                        metrics_from_data.append({
                            "name": context[:50],  # Limit name length
                            "value": value,
                            "context": context[:100],
                            "source": "extracted"
                        })
                except:
                    continue
        
        # Then use Gemini to identify and prioritize metrics
        metrics_text = "\\n".join([f"- {m['name']}: {m['value']}" for m in metrics_from_data[:5]])
        
        prompt = f"""From the content and metrics below, identify the 5-7 most important metrics for a business presentation.
        
        Content Summary:
        {content_summary[:500]}...
        
        Available Metrics:
        {metrics_text}
        
        For each metric, provide:
        - name: Metric name
        - value: The metric value
        - importance: Score from 0.0 to 1.0
        - category: Type of metric (e.g., "financial", "operational", "market")
        
        Respond with JSON array of metrics."""
        
        output_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "string"},
                    "importance": {"type": "number"},
                    "category": {"type": "string"}
                },
                "required": ["name", "value", "importance", "category"]
            }
        }
        
        try:
            response = self.call_gemini(prompt, output_schema)
            return response if isinstance(response, list) else metrics_from_data[:5]
        except:
            return metrics_from_data[:5]
    
    def _assess_content_depth(self, content_summary: str) -> str:
        """Assess the depth and complexity of the content."""
        word_count = len(content_summary.split())
        
        if word_count < 100:
            return "light"
        elif word_count < 300:
            return "moderate"
        else:
            return "deep"
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the insight extraction output."""
        if not output:
            return False
        
        required_keys = ["insights", "executive_summary", "themes", "metrics", "analysis_metadata"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in insight output: {key}")
                return False
        
        # Validate insights structure
        insights = output.get("insights", [])
        if not isinstance(insights, list):
            self.logger.error("insights is not a list")
            return False
        
        for insight in insights:
            if not isinstance(insight, dict):
                continue
            if "text" not in insight or "importance" not in insight:
                self.logger.error("Insight missing required fields")
                return False
        
        return True
