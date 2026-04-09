"""
Chart Decision Agent - Uses Gemini + Logic to decide on chart types and data.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional

from ..core.agent import GeminiAgent
from ..core.models import ChartType, ChartData


class ChartDecisionAgent(GeminiAgent):
    """Agent responsible for making intelligent chart decisions."""
    
    def __init__(self, gemini_client):
        system_prompt = """You are an expert data visualization specialist and chart designer.
        Your task is to analyze data and make intelligent decisions about chart types and presentation.
        
        Chart Type Guidelines:
        - bar: Comparing values across categories, ranking items
        - pie: Showing parts of a whole, percentages (max 5-7 categories)
        - line: Showing trends over time, continuous data
        - area: Showing cumulative totals, volume over time
        
        Decision Criteria:
        1. Data type and structure
        2. Number of data points
        3. Relationship between data points
        4. Story the data should tell
        5. Audience and context
        
        For each chart decision, provide:
        1. Recommended chart type
        2. Data preparation instructions
        3. Styling recommendations
        4. Key insights to highlight
        
        Always respond in valid JSON format with specified schema."""
        
        super().__init__("chart_decision_agent", gemini_client, system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make chart decisions based on data and visual elements."""
        try:
            self.log_reasoning("start", "Starting chart decision analysis")
            
            visual_data = input_data.get("visual_data", {})
            parsed_data = input_data.get("parsed_data", {})
            
            if not visual_data:
                raise ValueError("No visual data provided")
            
            # Extract numeric data
            self.log_reasoning("extract_numeric", "Extracting numeric data for charts")
            numeric_data = self._extract_all_numeric_data(visual_data, parsed_data)
            
            # Analyze chart opportunities
            self.log_reasoning("analyze_opportunities", "Analyzing chart opportunities", {
                "numeric_data_points": len(numeric_data),
                "slides_with_visuals": len(visual_data.get("visual_elements", []))
            })
            
            # Make chart decisions using Gemini + Logic
            self.log_reasoning("make_decisions", "Making chart decisions with AI + logic")
            chart_decisions = self._make_chart_decisions(numeric_data, visual_data)
            
            # Validate and optimize decisions
            self.log_reasoning("validate_decisions", "Validating and optimizing chart decisions")
            validated_decisions = self._validate_and_optimize_decisions(chart_decisions)
            
            # Create chart specifications
            self.log_reasoning("create_specifications", "Creating detailed chart specifications")
            chart_specifications = self._create_chart_specifications(validated_decisions)
            
            # Create decision summary
            self.log_reasoning("create_summary", "Creating chart decision summary")
            decision_summary = self._create_decision_summary(validated_decisions, chart_specifications)
            
            output = {
                "chart_decisions": validated_decisions,
                "chart_specifications": chart_specifications,
                "decision_summary": decision_summary,
                "chart_metadata": {
                    "total_charts": len(chart_specifications),
                    "chart_types_used": self._get_chart_types_used(chart_specifications),
                    "data_coverage": self._calculate_data_coverage(numeric_data, chart_specifications),
                    "decision_confidence": self._calculate_decision_confidence(validated_decisions)
                }
            }
            
            self.log_reasoning("complete", "Successfully made chart decisions", {
                "total_decisions": len(validated_decisions),
                "charts_created": len(chart_specifications),
                "chart_types": list(set(spec.get("chart_type") for spec in chart_specifications))
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in chart decision agent: {str(e)}")
            raise
    
    def _extract_all_numeric_data(self, visual_data: Dict, parsed_data: Dict) -> List[Dict[str, Any]]:
        """Extract all numeric data from various sources."""
        numeric_data = []
        
        # Extract from parsed data
        if "numeric_data" in parsed_data:
            for data_point in parsed_data["numeric_data"]:
                numeric_data.append({
                    "source": "parsed",
                    "type": data_point.get("type", "unknown"),
                    "values": data_point.get("value", []),
                    "context": data_point.get("context", ""),
                    "raw_data": data_point
                })
        
        # Extract from visual elements
        visual_elements = visual_data.get("visual_elements", [])
        for i, slide in enumerate(visual_elements):
            slide_num = slide.get("slide_number", i + 1)
            visual_elems = slide.get("visual_elements", [])
            
            for visual in visual_elems:
                if visual.get("type") == "infographic":
                    content = visual.get("content", [])
                    for item in content:
                        if "metric" in item or "value" in item:
                            numeric_data.append({
                                "source": "visual_infographic",
                                "slide_number": slide_num,
                                "metric": item.get("metric", ""),
                                "value": item.get("value", ""),
                                "context": f"Slide {slide_num} infographic"
                            })
        
        # Extract from slide plans (if available)
        for i, slide in enumerate(visual_elements):
            if "slide_plan" in slide:
                plan = slide["slide_plan"]
                chart_data = plan.get("chart_data")
                if chart_data:
                    numeric_data.append({
                        "source": "slide_plan",
                        "slide_number": i + 1,
                        "chart_type": chart_data.get("type", ""),
                        "title": chart_data.get("title", ""),
                        "data": chart_data.get("data", {}),
                        "raw_data": chart_data
                    })
        
        return numeric_data
    
    def _make_chart_decisions(self, numeric_data: List[Dict], visual_data: Dict) -> List[Dict[str, Any]]:
        """Make chart decisions using Gemini + logic."""
        # First, apply logic-based decisions
        logic_decisions = self._apply_logic_based_decisions(numeric_data)
        
        # Then, use Gemini for complex decisions
        gemini_decisions = self._use_gemini_for_decisions(numeric_data, visual_data, logic_decisions)
        
        # Combine and prioritize decisions
        combined_decisions = self._combine_decisions(logic_decisions, gemini_decisions)
        
        return combined_decisions
    
    def _apply_logic_based_decisions(self, numeric_data: List[Dict]) -> List[Dict[str, Any]]:
        """Apply logic-based rules for chart decisions."""
        decisions = []
        
        for data_point in numeric_data:
            source = data_point.get("source", "")
            
            if source == "parsed" and data_point.get("type") == "table_data":
                # Table data - good for bar charts
                values = data_point.get("values", [])
                context = data_point.get("context", "")
                
                if len(values) >= 2:
                    decisions.append({
                        "slide_number": self._infer_slide_number(data_point),
                        "chart_type": "bar",
                        "data_source": "table",
                        "confidence": 0.8,
                        "reasoning": f"Table data with {len(values)} values suitable for bar chart",
                        "data_point": data_point
                    })
            
            elif source == "visual_infographic":
                # Infographic metrics - good for pie or bar charts
                metric = data_point.get("metric", "")
                value = data_point.get("value", "")
                
                if metric and value:
                    # Try to determine if it's a percentage
                    is_percentage = "%" in str(value)
                    
                    chart_type = "pie" if is_percentage else "bar"
                    decisions.append({
                        "slide_number": data_point.get("slide_number", 1),
                        "chart_type": chart_type,
                        "data_source": "infographic",
                        "confidence": 0.7,
                        "reasoning": f"Infographic metric {metric} with value {value}",
                        "data_point": data_point
                    })
            
            elif source == "slide_plan":
                # Existing chart data
                chart_type = data_point.get("chart_type", "")
                if chart_type in [t.value for t in ChartType]:
                    decisions.append({
                        "slide_number": data_point.get("slide_number", 1),
                        "chart_type": chart_type,
                        "data_source": "plan",
                        "confidence": 0.9,
                        "reasoning": "Existing chart plan",
                        "data_point": data_point
                    })
        
        return decisions
    
    def _use_gemini_for_decisions(self, numeric_data: List[Dict], visual_data: Dict, logic_decisions: List[Dict]) -> List[Dict[str, Any]]:
        """Use Gemini for complex chart decisions."""
        # Prepare context for Gemini
        gemini_context = self._prepare_gemini_chart_context(numeric_data, visual_data, logic_decisions)
        
        prompt = f"""Analyze the data and visual context below to make intelligent chart decisions.
        For each potential chart, provide:
        1. slide_number: Which slide should have this chart
        2. chart_type: One of: bar, pie, line, area
        3. confidence: 0.0 to 1.0 confidence in this decision
        4. reasoning: Why this chart type is optimal
        5. data_preparation: How to prepare the data
        
        {gemini_context}
        
        Consider:
        - Data relationships and patterns
        - Story the data should tell
        - Visual clarity and impact
        - Avoid chart overload
        
        Respond with JSON array of chart decisions."""
        
        output_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slide_number": {"type": "number"},
                    "chart_type": {"type": "string"},
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"},
                    "data_preparation": {"type": "object"}
                },
                "required": ["slide_number", "chart_type", "confidence", "reasoning"]
            }
        }
        
        try:
            response = self.call_gemini(prompt, output_schema)
            if isinstance(response, list):
                return response
        except Exception as e:
            self.logger.error(f"Error calling Gemini for chart decisions: {str(e)}")
        
        return []
    
    def _prepare_gemini_chart_context(self, numeric_data: List[Dict], visual_data: Dict, logic_decisions: List[Dict]) -> str:
        """Prepare context for Gemini chart decision making."""
        context_parts = []
        
        context_parts.append("Chart Decision Context:")
        
        # Add numeric data overview
        context_parts.append(f"\\nNumeric Data Available ({len(numeric_data)} points):")
        for i, data in enumerate(numeric_data[:10]):  # Limit to first 10
            source = data.get("source", "")
            values = data.get("values", [])[:3]  # Limit values display
            context = data.get("context", "")[:50]
            context_parts.append(f"  {i+1}. [{source}] {context} - Values: {values}")
        
        # Add visual elements context
        visual_elements = visual_data.get("visual_elements", [])
        context_parts.append(f"\\nVisual Elements ({len(visual_elements)} slides):")
        for i, slide in enumerate(visual_elements[:5]):  # Limit to first 5 slides
            slide_num = slide.get("slide_number", i + 1)
            visuals = slide.get("visual_elements", [])
            visual_types = [v.get("type", "") for v in visuals]
            context_parts.append(f"  Slide {slide_num}: {visual_types}")
        
        # Add logic decisions
        context_parts.append(f"\\nLogic-Based Decisions ({len(logic_decisions)}):")
        for decision in logic_decisions:
            slide_num = decision.get("slide_number", 0)
            chart_type = decision.get("chart_type", "")
            confidence = decision.get("confidence", 0)
            reasoning = decision.get("reasoning", "")[:50]
            context_parts.append(f"  Slide {slide_num}: {chart_type} (conf: {confidence}) - {reasoning}")
        
        # Add decision guidelines
        context_parts.append("\\nDecision Guidelines:")
        context_parts.append("- bar: Comparing categories, ranking, discrete values")
        context_parts.append("- pie: Parts of whole, percentages, composition")
        context_parts.append("- line: Trends over time, continuous data")
        context_parts.append("- area: Cumulative totals, volume over time")
        context_parts.append("- Max 1-2 charts per slide for clarity")
        context_parts.append("- Prioritize data that tells a clear story")
        
        return "\\n".join(context_parts)
    
    def _combine_decisions(self, logic_decisions: List[Dict], gemini_decisions: List[Dict]) -> List[Dict[str, Any]]:
        """Combine logic and Gemini decisions, prioritizing and avoiding duplicates."""
        combined = []
        slide_charts = {}  # Track charts per slide
        
        # Add logic decisions first (higher confidence for clear cases)
        for decision in logic_decisions:
            slide_num = decision.get("slide_number", 0)
            chart_type = decision.get("chart_type", "")
            
            # Limit charts per slide
            if slide_num not in slide_charts:
                slide_charts[slide_num] = []
            
            if len(slide_charts[slide_num]) < 2:  # Max 2 charts per slide
                combined.append(decision)
                slide_charts[slide_num].append(chart_type)
        
        # Add Gemini decisions for gaps and complex cases
        for decision in gemini_decisions:
            slide_num = decision.get("slide_number", 0)
            chart_type = decision.get("chart_type", "")
            confidence = decision.get("confidence", 0)
            
            # Skip if low confidence or duplicate
            if confidence < 0.6:
                continue
            
            if slide_num not in slide_charts:
                slide_charts[slide_num] = []
            
            # Check for duplicate chart types on same slide
            if chart_type not in slide_charts[slide_num] and len(slide_charts[slide_num]) < 2:
                combined.append(decision)
                slide_charts[slide_num].append(chart_type)
        
        # Sort by slide number
        combined.sort(key=lambda x: x.get("slide_number", 0))
        
        return combined
    
    def _validate_and_optimize_decisions(self, decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and optimize chart decisions."""
        validated = []
        
        for decision in decisions:
            # Validate required fields
            if not all(key in decision for key in ["slide_number", "chart_type", "confidence", "reasoning"]):
                self.logger.warning(f"Decision missing required fields: {decision}")
                continue
            
            # Validate chart type
            chart_type = decision.get("chart_type", "")
            if chart_type not in [t.value for t in ChartType]:
                # Adjust to valid type
                chart_type = self._fallback_chart_type(decision)
                decision["chart_type"] = chart_type
                decision["reasoning"] += f" (Adjusted to {chart_type})"
            
            # Optimize confidence based on data quality
            confidence = decision.get("confidence", 0)
            data_point = decision.get("data_point", {})
            
            if data_point:
                # Boost confidence for structured data
                if data_point.get("type") == "table_data":
                    confidence = min(1.0, confidence + 0.1)
                elif data_point.get("source") == "plan":
                    confidence = min(1.0, confidence + 0.2)
            
            decision["confidence"] = round(confidence, 2)
            
            validated.append(decision)
        
        return validated
    
    def _fallback_chart_type(self, decision: Dict[str, Any]) -> str:
        """Provide fallback chart type."""
        data_point = decision.get("data_point", {})
        values = data_point.get("values", [])
        
        if len(values) > 5:
            return "bar"  # Many categories -> bar chart
        elif any("%" in str(v) for v in values):
            return "pie"  # Percentages -> pie chart
        else:
            return "bar"  # Default to bar
    
    def _create_chart_specifications(self, validated_decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create detailed chart specifications from decisions."""
        specifications = []
        
        for decision in validated_decisions:
            slide_num = decision.get("slide_number", 0)
            chart_type = decision.get("chart_type", "")
            data_point = decision.get("data_point", {})
            
            # Create chart specification
            spec = {
                "slide_number": slide_num,
                "chart_type": chart_type,
                "title": self._generate_chart_title(decision),
                "data": self._prepare_chart_data(decision),
                "styling": self._generate_chart_styling(chart_type),
                "positioning": self._generate_chart_positioning(decision),
                "metadata": {
                    "confidence": decision.get("confidence", 0),
                    "reasoning": decision.get("reasoning", ""),
                    "data_source": decision.get("data_source", "unknown")
                }
            }
            
            specifications.append(spec)
        
        return specifications
    
    def _generate_chart_title(self, decision: Dict[str, Any]) -> str:
        """Generate appropriate chart title."""
        data_point = decision.get("data_point", {})
        context = data_point.get("context", "")
        chart_type = decision.get("chart_type", "")
        
        if context:
            # Extract key phrase from context
            words = context.split()
            if len(words) <= 6:
                return context.title()
            else:
                return " ".join(words[:6]).title()
        
        # Fallback titles based on chart type
        title_map = {
            "bar": "Comparison Analysis",
            "pie": "Distribution Overview",
            "line": "Trend Analysis",
            "area": "Cumulative Analysis"
        }
        
        return title_map.get(chart_type, "Data Visualization")
    
    def _prepare_chart_data(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare chart data from decision."""
        data_point = decision.get("data_point", {})
        chart_type = decision.get("chart_type", "")
        
        if data_point.get("source") == "parsed":
            # Extract from parsed data
            values = data_point.get("values", [])
            context = data_point.get("context", "")
            
            # Try to extract labels
            labels = []
            data_values = []
            
            for i, value in enumerate(values[:5]):  # Limit to 5 values
                label = f"Item {i+1}"
                data_values.append(self._clean_numeric_value(value))
                labels.append(label)
            
            return {
                "labels": labels,
                "datasets": [{
                    "label": "Values",
                    "data": data_values,
                    "backgroundColor": self._get_chart_colors(chart_type)
                }]
            }
        
        elif data_point.get("source") == "visual_infographic":
            # Extract from infographic
            metric = data_point.get("metric", "")
            value = data_point.get("value", "")
            
            return {
                "labels": [metric],
                "datasets": [{
                    "label": metric,
                    "data": [self._clean_numeric_value(value)],
                    "backgroundColor": self._get_chart_colors(chart_type)
                }]
            }
        
        else:
            # Default/placeholder data
            return {
                "labels": ["Category A", "Category B", "Category C"],
                "datasets": [{
                    "label": "Data",
                    "data": [10, 20, 15],
                    "backgroundColor": self._get_chart_colors(chart_type)
                }]
            }
    
    def _clean_numeric_value(self, value: str) -> float:
        """Clean and convert string to numeric value."""
        try:
            # Remove common formatting
            clean_value = str(value).replace("%", "").replace(",", "").replace("$", "")
            return float(clean_value)
        except:
            return 0.0
    
    def _get_chart_colors(self, chart_type: str) -> List[str]:
        """Get appropriate colors for chart type."""
        color_schemes = {
            "bar": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
            "pie": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
            "line": ["#1f77b4", "#ff7f0e", "#2ca02c"],
            "area": ["#1f77b4", "#ff7f0e", "#2ca02c"]
        }
        
        return color_schemes.get(chart_type, ["#1f77b4", "#ff7f0e", "#2ca02c"])
    
    def _generate_chart_styling(self, chart_type: str) -> Dict[str, Any]:
        """Generate styling recommendations for chart."""
        base_styling = {
            "responsive": True,
            "maintainAspectRatio": False,
            "legend": {
                "display": True,
                "position": "bottom"
            }
        }
        
        type_specific = {
            "bar": {
                "scales": {
                    "y": {"beginAtZero": True},
                    "x": {"display": True}
                }
            },
            "pie": {
                "scales": {"display": False}
            },
            "line": {
                "elements": {
                    "line": {"tension": 0.1},
                    "point": {"radius": 4}
                }
            },
            "area": {
                "elements": {
                    "line": {"tension": 0.1, "fill": True},
                    "point": {"radius": 3}
                }
            }
        }
        
        return {**base_styling, **type_specific.get(chart_type, {})}
    
    def _generate_chart_positioning(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Generate positioning instructions for chart."""
        slide_num = decision.get("slide_number", 0)
        confidence = decision.get("confidence", 0)
        
        # Higher confidence charts get better positioning
        if confidence >= 0.8:
            return {
                "position": "center",
                "size": "large",
                "priority": "high"
            }
        elif confidence >= 0.6:
            return {
                "position": "right",
                "size": "medium",
                "priority": "medium"
            }
        else:
            return {
                "position": "bottom",
                "size": "small",
                "priority": "low"
            }
    
    def _create_decision_summary(self, validated_decisions: List[Dict], chart_specifications: List[Dict]) -> Dict[str, Any]:
        """Create a summary of chart decisions."""
        chart_types = {}
        confidence_scores = []
        
        for decision in validated_decisions:
            chart_type = decision.get("chart_type", "")
            confidence = decision.get("confidence", 0)
            
            chart_types[chart_type] = chart_types.get(chart_type, 0) + 1
            confidence_scores.append(confidence)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            "total_decisions": len(validated_decisions),
            "total_charts": len(chart_specifications),
            "chart_type_distribution": chart_types,
            "average_confidence": round(avg_confidence, 2),
            "high_confidence_charts": len([c for c in confidence_scores if c >= 0.8]),
            "slides_with_charts": len(set(d.get("slide_number", 0) for d in validated_decisions))
        }
    
    def _infer_slide_number(self, data_point: Dict) -> int:
        """Infer slide number from data point."""
        # Try to extract from context or use default
        context = data_point.get("context", "")
        if "slide" in context.lower():
            import re
            slide_match = re.search(r'slide (\d+)', context.lower())
            if slide_match:
                return int(slide_match.group(1))
        
        return 1  # Default to slide 1
    
    def _get_chart_types_used(self, specifications: List[Dict]) -> List[str]:
        """Get list of chart types used."""
        return list(set(spec.get("chart_type", "") for spec in specifications))
    
    def _calculate_data_coverage(self, numeric_data: List[Dict], specifications: List[Dict]) -> float:
        """Calculate percentage of numeric data covered by charts."""
        if not numeric_data:
            return 0.0
        
        # Simple calculation: each chart covers at least one data point
        covered_points = min(len(numeric_data), len(specifications))
        return round((covered_points / len(numeric_data)) * 100, 1)
    
    def _calculate_decision_confidence(self, validated_decisions: List[Dict]) -> float:
        """Calculate average confidence of decisions."""
        if not validated_decisions:
            return 0.0
        
        confidences = [d.get("confidence", 0) for d in validated_decisions]
        return round(sum(confidences) / len(confidences), 2)
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate chart decision output."""
        if not output:
            return False
        
        required_keys = ["chart_decisions", "chart_specifications", "decision_summary", "chart_metadata"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in chart decision output: {key}")
                return False
        
        # Validate chart decisions
        chart_decisions = output.get("chart_decisions", [])
        if not isinstance(chart_decisions, list):
            self.logger.error("chart_decisions is not a list")
            return False
        
        # Validate each decision
        valid_types = [t.value for t in ChartType]
        for i, decision in enumerate(chart_decisions):
            if not isinstance(decision, dict):
                self.logger.error(f"Chart decision {i} is not a dictionary")
                return False
            
            chart_type = decision.get("chart_type", "")
            if chart_type not in valid_types:
                self.logger.error(f"Invalid chart type: {chart_type}")
                return False
        
        return True
