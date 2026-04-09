"""
Layout Engine - Deterministic engine for enforcing grid systems, spacing, and alignment.
"""

import logging
from typing import Dict, Any, List, Tuple
import math

from ..core.agent import BaseAgent
from ..core.models import SlideLayout, VisualElement, ChartData


class LayoutEngine(BaseAgent):
    """Deterministic layout engine for consistent slide design."""
    
    def __init__(self):
        super().__init__("layout_engine")
        
        # Grid system configuration
        self.grid_config = {
            "columns": 12,  # 12-column grid system
            "rows": 8,     # 8-row grid system
            "margin": 0.5,   # 0.5 inch margins
            "gutter": 0.25, # 0.25 inch gutters
            "safe_area": 0.75 # 0.75 inch safe area from edges
        }
        
        # Slide dimensions (in inches for PowerPoint)
        self.slide_dimensions = {
            "width": 10.0,
            "height": 7.5
        }
        
        # Content area dimensions
        self.content_area = {
            "width": self.slide_dimensions["width"] - (2 * self.grid_config["margin"]),
            "height": self.slide_dimensions["height"] - (2 * self.grid_config["margin"]),
            "left": self.grid_config["margin"],
            "top": self.grid_config["margin"]
        }
        
        # Layout templates
        self.layout_templates = self._initialize_layout_templates()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process visual elements and chart data into structured layouts."""
        try:
            self.log_reasoning("start", "Starting layout engine processing")
            
            visual_data = input_data.get("visual_data", {})
            chart_data = input_data.get("chart_data", {})
            
            if not visual_data:
                raise ValueError("No visual data provided")
            
            # Process each slide
            self.log_reasoning("process_slides", "Processing slide layouts", {
                "total_slides": len(visual_data.get("visual_elements", [])),
                "total_charts": len(chart_data.get("chart_specifications", []))
            })
            
            processed_slides = []
            visual_elements = visual_data.get("visual_elements", [])
            
            for i, slide_data in enumerate(visual_elements):
                slide_layout = self._process_slide_layout(
                    slide_data, 
                    chart_data, 
                    i + 1  # Slide numbers are 1-based
                )
                processed_slides.append(slide_layout)
            
            # Create layout summary
            self.log_reasoning("create_summary", "Creating layout summary")
            layout_summary = self._create_layout_summary(processed_slides)
            
            output = {
                "layout_data": processed_slides,
                "layout_summary": layout_summary,
                "layout_metadata": {
                    "total_slides": len(processed_slides),
                    "grid_system": self.grid_config,
                    "slide_dimensions": self.slide_dimensions,
                    "layout_consistency_score": self._calculate_consistency_score(processed_slides),
                    "space_utilization": self._calculate_space_utilization(processed_slides)
                }
            }
            
            self.log_reasoning("complete", "Successfully processed layouts", {
                "total_layouts": len(processed_slides),
                "consistency_score": output["layout_metadata"]["layout_consistency_score"],
                "space_utilization": output["layout_metadata"]["space_utilization"]
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in layout engine: {str(e)}")
            raise
    
    def _process_slide_layout(self, slide_data: Dict[str, Any], chart_data: Dict, slide_number: int) -> Dict[str, Any]:
        """Process layout for a single slide."""
        # Extract slide information
        visual_elements = slide_data.get("visual_elements", [])
        text_content = slide_data.get("text_content", "")
        slide_type = self._determine_slide_type(slide_data, slide_number)
        
        # Select appropriate layout template
        layout_template = self._select_layout_template(slide_type, len(visual_elements), bool(text_content))
        
        # Create slide layout
        slide_layout = {
            "slide_number": slide_number,
            "slide_type": slide_type,
            "layout_template": layout_template["name"],
            "grid_layout": self._create_grid_layout(layout_template),
            "content_areas": self._create_content_areas(layout_template, visual_elements, text_content),
            "positioning": self._calculate_positions(layout_template, visual_elements, text_content),
            "spacing": self._calculate_spacing(layout_template),
            "alignment": self._calculate_alignment(layout_template)
        }
        
        # Add chart positioning if applicable
        chart_spec = self._find_chart_for_slide(chart_data, slide_number)
        if chart_spec:
            slide_layout["chart_positioning"] = self._position_chart(chart_spec, layout_template)
        
        return slide_layout
    
    def _determine_slide_type(self, slide_data: Dict[str, Any], slide_number: int) -> str:
        """Determine slide type for layout purposes."""
        # Check if it's a title slide
        if slide_number == 1:
            return "title"
        
        # Check if it's an agenda slide
        if slide_number == 2:
            return "agenda"
        
        # Check if it's a conclusion slide
        text_content = slide_data.get("text_content", "").lower()
        if any(word in text_content for word in ["conclusion", "summary", "recommendation"]):
            return "conclusion"
        
        # Determine based on visual elements
        visual_elements = slide_data.get("visual_elements", [])
        if not visual_elements:
            return "text_only"
        
        # Count different visual types
        visual_types = [v.get("type", "") for v in visual_elements]
        
        if "flow" in visual_types:
            return "process"
        elif "timeline" in visual_types:
            return "timeline"
        elif "grid" in visual_types:
            return "comparison"
        elif "infographic" in visual_types:
            return "data"
        else:
            return "mixed"
    
    def _select_layout_template(self, slide_type: str, visual_count: int, has_text: bool) -> Dict[str, Any]:
        """Select appropriate layout template."""
        templates = self.layout_templates.get(slide_type, self.layout_templates["mixed"])
        
        # Choose specific variant based on content
        if visual_count == 0 and has_text:
            return templates["text_only"]
        elif visual_count == 1 and has_text:
            return templates["single_visual_text"]
        elif visual_count == 1:
            return templates["single_visual"]
        elif visual_count == 2:
            return templates["two_visual"]
        else:
            return templates["multiple_visual"]
    
    def _create_grid_layout(self, layout_template: Dict[str, Any]) -> Dict[str, Any]:
        """Create grid layout based on template."""
        grid_spec = layout_template.get("grid", {})
        
        return {
            "columns": grid_spec.get("columns", self.grid_config["columns"]),
            "rows": grid_spec.get("rows", self.grid_config["rows"]),
            "column_widths": grid_spec.get("column_widths", []),
            "row_heights": grid_spec.get("row_heights", []),
            "gutter_width": self.grid_config["gutter"],
            "margin": self.grid_config["margin"]
        }
    
    def _create_content_areas(self, layout_template: Dict[str, Any], visual_elements: List[Dict], text_content: str) -> List[Dict[str, Any]]:
        """Create content areas based on template and content."""
        areas = []
        template_areas = layout_template.get("areas", [])
        
        # Map content to areas
        for i, area_spec in enumerate(template_areas):
            area = {
                "id": f"area_{i+1}",
                "type": area_spec.get("type", "content"),
                "grid_position": area_spec.get("grid_position", {}),
                "size": area_spec.get("size", {}),
                "content": None,
                "priority": area_spec.get("priority", "medium")
            }
            
            # Assign content to area
            if i < len(visual_elements):
                area["content"] = visual_elements[i]
                area["type"] = "visual"
            elif text_content and i == len(template_areas) - 1:
                area["content"] = {"text": text_content}
                area["type"] = "text"
            
            areas.append(area)
        
        return areas
    
    def _calculate_positions(self, layout_template: Dict[str, Any], visual_elements: List[Dict], text_content: str) -> Dict[str, Any]:
        """Calculate precise positions for all content."""
        positions = {}
        grid_cols = self.grid_config["columns"]
        grid_rows = self.grid_config["rows"]
        cell_width = (self.content_area["width"] - (grid_cols - 1) * self.grid_config["gutter"]) / grid_cols
        cell_height = (self.content_area["height"] - (grid_rows - 1) * self.grid_config["gutter"]) / grid_rows
        
        # Calculate positions for each content area
        template_areas = layout_template.get("areas", [])
        
        for i, area_spec in enumerate(template_areas):
            grid_pos = area_spec.get("grid_position", {})
            
            if grid_pos:
                # Convert grid position to pixels/inches
                col_start = grid_pos.get("col_start", 0)
                col_end = grid_pos.get("col_end", 1)
                row_start = grid_pos.get("row_start", 0)
                row_end = grid_pos.get("row_end", 1)
                
                # Calculate actual position
                left = self.content_area["left"] + col_start * (cell_width + self.grid_config["gutter"])
                top = self.content_area["top"] + row_start * (cell_height + self.grid_config["gutter"])
                width = (col_end - col_start) * cell_width + (col_end - col_start - 1) * self.grid_config["gutter"]
                height = (row_end - row_start) * cell_height + (row_end - row_start - 1) * self.grid_config["gutter"]
                
                positions[f"area_{i+1}"] = {
                    "left": round(left, 2),
                    "top": round(top, 2),
                    "width": round(width, 2),
                    "height": round(height, 2),
                    "grid_coords": {
                        "col_start": col_start,
                        "col_end": col_end,
                        "row_start": row_start,
                        "row_end": row_end
                    }
                }
        
        return positions
    
    def _calculate_spacing(self, layout_template: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate spacing specifications."""
        base_spacing = layout_template.get("spacing", {})
        
        return {
            "margin": self.grid_config["margin"],
            "gutter": self.grid_config["gutter"],
            "padding": base_spacing.get("padding", 0.25),
            "element_spacing": base_spacing.get("element_spacing", 0.5),
            "line_spacing": base_spacing.get("line_spacing", 1.2)
        }
    
    def _calculate_alignment(self, layout_template: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate alignment specifications."""
        base_alignment = layout_template.get("alignment", {})
        
        return {
            "horizontal": base_alignment.get("horizontal", "left"),
            "vertical": base_alignment.get("vertical", "top"),
            "text_alignment": base_alignment.get("text_alignment", "left"),
            "visual_alignment": base_alignment.get("visual_alignment", "center")
        }
    
    def _find_chart_for_slide(self, chart_data: Dict, slide_number: int) -> Optional[Dict[str, Any]]:
        """Find chart specification for a specific slide."""
        chart_specs = chart_data.get("chart_specifications", [])
        
        for spec in chart_specs:
            if spec.get("slide_number") == slide_number:
                return spec
        
        return None
    
    def _position_chart(self, chart_spec: Dict[str, Any], layout_template: Dict[str, Any]) -> Dict[str, Any]:
        """Position chart within the layout."""
        positioning = chart_spec.get("positioning", {})
        chart_position = positioning.get("position", "right")
        chart_size = positioning.get("size", "medium")
        
        # Define chart sizes
        size_map = {
            "small": {"width": 3.0, "height": 2.25},
            "medium": {"width": 4.0, "height": 3.0},
            "large": {"width": 6.0, "height": 4.5}
        }
        
        chart_dimensions = size_map.get(chart_size, size_map["medium"])
        
        # Calculate position based on layout
        if chart_position == "center":
            left = (self.slide_dimensions["width"] - chart_dimensions["width"]) / 2
            top = (self.slide_dimensions["height"] - chart_dimensions["height"]) / 2
        elif chart_position == "right":
            left = self.slide_dimensions["width"] - chart_dimensions["width"] - self.grid_config["margin"]
            top = self.grid_config["margin"] + 1.0
        else:  # left or default
            left = self.grid_config["margin"]
            top = self.grid_config["margin"] + 1.0
        
        return {
            "left": round(left, 2),
            "top": round(top, 2),
            "width": round(chart_dimensions["width"], 2),
            "height": round(chart_dimensions["height"], 2),
            "position": chart_position,
            "size": chart_size,
            "z_index": 1  # Charts should be on top
        }
    
    def _create_layout_summary(self, processed_slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of layout processing."""
        slide_types = {}
        template_usage = {}
        total_elements = 0
        
        for slide in processed_slides:
            slide_type = slide.get("slide_type", "unknown")
            template = slide.get("layout_template", "unknown")
            elements = len(slide.get("content_areas", []))
            
            slide_types[slide_type] = slide_types.get(slide_type, 0) + 1
            template_usage[template] = template_usage.get(template, 0) + 1
            total_elements += elements
        
        return {
            "total_slides": len(processed_slides),
            "slide_type_distribution": slide_types,
            "template_usage": template_usage,
            "total_content_elements": total_elements,
            "avg_elements_per_slide": round(total_elements / len(processed_slides), 1) if processed_slides else 0
        }
    
    def _calculate_consistency_score(self, processed_slides: List[Dict[str, Any]]) -> float:
        """Calculate layout consistency score."""
        if not processed_slides:
            return 0.0
        
        # Check consistency in margins, gutters, and spacing
        margin_consistency = len(set(slide.get("spacing", {}).get("margin", 0) for slide in processed_slides)) == 1
        gutter_consistency = len(set(slide.get("spacing", {}).get("gutter", 0) for slide in processed_slides)) == 1
        
        # Check template variety (not too many different templates)
        templates = [slide.get("layout_template", "") for slide in processed_slides]
        unique_templates = len(set(templates))
        template_variety_score = max(0, 1 - (unique_templates - 3) * 0.1)  # Penalize too many templates
        
        # Calculate overall score
        consistency_score = 0.0
        if margin_consistency:
            consistency_score += 0.4
        if gutter_consistency:
            consistency_score += 0.4
        consistency_score += template_variety_score * 0.2
        
        return round(consistency_score, 2)
    
    def _calculate_space_utilization(self, processed_slides: List[Dict[str, Any]]) -> float:
        """Calculate average space utilization."""
        if not processed_slides:
            return 0.0
        
        total_utilization = 0.0
        
        for slide in processed_slides:
            content_areas = slide.get("content_areas", [])
            slide_utilization = 0.0
            
            for area in content_areas:
                positions = slide.get("positioning", {})
                area_key = f"area_{area['id'].split('_')[1]}"
                
                if area_key in positions:
                    area_pos = positions[area_key]
                    area_width = area_pos.get("width", 0)
                    area_height = area_pos.get("height", 0)
                    area_size = area_width * area_height
                    
                    # Calculate as percentage of content area
                    content_area_size = self.content_area["width"] * self.content_area["height"]
                    area_utilization = (area_size / content_area_size) * 100
                    slide_utilization += area_utilization
            
            total_utilization += slide_utilization
        
        avg_utilization = total_utilization / len(processed_slides)
        return round(avg_utilization, 1)
    
    def _initialize_layout_templates(self) -> Dict[str, Any]:
        """Initialize layout templates for different slide types."""
        return {
            "title": {
                "text_only": {
                    "name": "title_centered",
                    "grid": {"columns": 12, "rows": 8},
                    "areas": [
                        {
                            "type": "title",
                            "grid_position": {"col_start": 2, "col_end": 10, "row_start": 2, "row_end": 4},
                            "size": {"width": 8, "height": 2},
                            "priority": "high"
                        },
                        {
                            "type": "subtitle",
                            "grid_position": {"col_start": 3, "col_end": 9, "row_start": 4, "row_end": 5},
                            "size": {"width": 6, "height": 1},
                            "priority": "medium"
                        }
                    ],
                    "spacing": {"padding": 0.5, "element_spacing": 1.0},
                    "alignment": {"horizontal": "center", "vertical": "middle", "text_alignment": "center"}
                }
            },
            "agenda": {
                "single_visual_text": {
                    "name": "agenda_list",
                    "grid": {"columns": 12, "rows": 8},
                    "areas": [
                        {
                            "type": "title",
                            "grid_position": {"col_start": 1, "col_end": 11, "row_start": 0, "row_end": 1},
                            "size": {"width": 10, "height": 1},
                            "priority": "high"
                        },
                        {
                            "type": "content",
                            "grid_position": {"col_start": 2, "col_end": 10, "row_start": 2, "row_end": 7},
                            "size": {"width": 8, "height": 5},
                            "priority": "medium"
                        }
                    ],
                    "spacing": {"padding": 0.25, "element_spacing": 0.5, "line_spacing": 1.5},
                    "alignment": {"horizontal": "left", "vertical": "top", "text_alignment": "left"}
                }
            },
            "process": {
                "single_visual": {
                    "name": "process_flow",
                    "grid": {"columns": 12, "rows": 8},
                    "areas": [
                        {
                            "type": "title",
                            "grid_position": {"col_start": 1, "col_end": 11, "row_start": 0, "row_end": 1},
                            "size": {"width": 10, "height": 1},
                            "priority": "high"
                        },
                        {
                            "type": "visual",
                            "grid_position": {"col_start": 1, "col_end": 11, "row_start": 2, "row_end": 7},
                            "size": {"width": 10, "height": 5},
                            "priority": "high"
                        }
                    ],
                    "spacing": {"padding": 0.5, "element_spacing": 0.75},
                    "alignment": {"horizontal": "center", "vertical": "middle", "visual_alignment": "center"}
                }
            },
            "data": {
                "single_visual_text": {
                    "name": "data_visualization",
                    "grid": {"columns": 12, "rows": 8},
                    "areas": [
                        {
                            "type": "title",
                            "grid_position": {"col_start": 1, "col_end": 11, "row_start": 0, "row_end": 1},
                            "size": {"width": 10, "height": 1},
                            "priority": "high"
                        },
                        {
                            "type": "visual",
                            "grid_position": {"col_start": 1, "col_end": 7, "row_start": 2, "row_end": 6},
                            "size": {"width": 6, "height": 4},
                            "priority": "high"
                        },
                        {
                            "type": "text",
                            "grid_position": {"col_start": 8, "col_end": 11, "row_start": 2, "row_end": 6},
                            "size": {"width": 3, "height": 4},
                            "priority": "medium"
                        }
                    ],
                    "spacing": {"padding": 0.25, "element_spacing": 0.5},
                    "alignment": {"horizontal": "left", "vertical": "top", "visual_alignment": "center"}
                }
            },
            "comparison": {
                "two_visual": {
                    "name": "comparison_grid",
                    "grid": {"columns": 12, "rows": 8},
                    "areas": [
                        {
                            "type": "title",
                            "grid_position": {"col_start": 1, "col_end": 11, "row_start": 0, "row_end": 1},
                            "size": {"width": 10, "height": 1},
                            "priority": "high"
                        },
                        {
                            "type": "visual",
                            "grid_position": {"col_start": 1, "col_end": 6, "row_start": 2, "row_end": 7},
                            "size": {"width": 5, "height": 5},
                            "priority": "high"
                        },
                        {
                            "type": "visual",
                            "grid_position": {"col_start": 7, "col_end": 11, "row_start": 2, "row_end": 7},
                            "size": {"width": 4, "height": 5},
                            "priority": "high"
                        }
                    ],
                    "spacing": {"padding": 0.5, "element_spacing": 0.75},
                    "alignment": {"horizontal": "center", "vertical": "middle", "visual_alignment": "center"}
                }
            },
            "conclusion": {
                "single_visual_text": {
                    "name": "conclusion_summary",
                    "grid": {"columns": 12, "rows": 8},
                    "areas": [
                        {
                            "type": "title",
                            "grid_position": {"col_start": 1, "col_end": 11, "row_start": 0, "row_end": 1},
                            "size": {"width": 10, "height": 1},
                            "priority": "high"
                        },
                        {
                            "type": "content",
                            "grid_position": {"col_start": 2, "col_end": 10, "row_start": 2, "row_end": 6},
                            "size": {"width": 8, "height": 4},
                            "priority": "medium"
                        }
                    ],
                    "spacing": {"padding": 0.5, "element_spacing": 0.75, "line_spacing": 1.4},
                    "alignment": {"horizontal": "center", "vertical": "middle", "text_alignment": "center"}
                }
            },
            "mixed": {
                "multiple_visual": {
                    "name": "flexible_layout",
                    "grid": {"columns": 12, "rows": 8},
                    "areas": [
                        {
                            "type": "title",
                            "grid_position": {"col_start": 1, "col_end": 11, "row_start": 0, "row_end": 1},
                            "size": {"width": 10, "height": 1},
                            "priority": "high"
                        },
                        {
                            "type": "content",
                            "grid_position": {"col_start": 1, "col_end": 11, "row_start": 2, "row_end": 7},
                            "size": {"width": 10, "height": 5},
                            "priority": "medium"
                        }
                    ],
                    "spacing": {"padding": 0.25, "element_spacing": 0.5},
                    "alignment": {"horizontal": "left", "vertical": "top", "text_alignment": "left"}
                }
            }
        }
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate layout engine output."""
        if not output:
            return False
        
        required_keys = ["layout_data", "layout_summary", "layout_metadata"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in layout engine output: {key}")
                return False
        
        # Validate layout data
        layout_data = output.get("layout_data", [])
        if not isinstance(layout_data, list):
            self.logger.error("layout_data is not a list")
            return False
        
        # Validate each slide layout
        for i, slide in enumerate(layout_data):
            if not isinstance(slide, dict):
                self.logger.error(f"Slide layout {i} is not a dictionary")
                return False
            
            required_slide_keys = ["slide_number", "slide_type", "layout_template", "grid_layout", "content_areas"]
            for key in required_slide_keys:
                if key not in slide:
                    self.logger.error(f"Slide layout {i} missing required key: {key}")
                    return False
        
        return True
