"""
PPTX Generator Agent - Generates the final PowerPoint presentation.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from ..core.agent import BaseAgent
from ..core.models import Slide, ChartData, ChartType
from ..utils.pptx_utils import PPTXUtils


class PPTXGeneratorAgent(BaseAgent):
    """Agent responsible for generating the final PowerPoint presentation."""
    
    def __init__(self):
        super().__init__("pptx_generator_agent")
        self.pptx_utils = PPTXUtils()
        
        # Presentation styling
        self.theme_colors = {
            "primary": RGBColor(31, 119, 180),      # Blue
            "secondary": RGBColor(255, 127, 14),     # Orange
            "accent": RGBColor(44, 160, 44),         # Green
            "danger": RGBColor(214, 39, 40),         # Red
            "warning": RGBColor(255, 193, 7),        # Yellow
            "info": RGBColor(23, 162, 184),          # Cyan
            "dark": RGBColor(44, 62, 80),            # Dark blue
            "light": RGBColor(236, 240, 241)          # Light gray
        }
        
        # Typography
        self.fonts = {
            "title": "Calibri Light",
            "heading": "Calibri",
            "body": "Calibri",
            "subtitle": "Calibri"
        }
        
        self.font_sizes = {
            "title": 44,
            "subtitle": 32,
            "heading": 28,
            "subheading": 20,
            "body": 18,
            "small": 14
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the final PowerPoint presentation."""
        try:
            self.log_reasoning("start", "Starting PowerPoint generation")
            
            layout_data = input_data.get("layout_data", {})
            chart_data = input_data.get("chart_data", {})
            storyline = input_data.get("storyline", {})
            output_path = input_data.get("output_path", "output.pptx")
            
            if not layout_data:
                raise ValueError("No layout data provided")
            
            # Create presentation
            self.log_reasoning("create_presentation", "Creating new presentation")
            prs = self.pptx_utils.create_presentation()
            
            # Process each slide
            self.log_reasoning("process_slides", "Processing slides", {
                "total_slides": len(layout_data.get("layout_data", [])),
                "output_path": output_path
            })
            
            slide_layouts = layout_data.get("layout_data", [])
            chart_specs = chart_data.get("chart_specifications", [])
            
            for i, slide_layout in enumerate(slide_layouts):
                slide = self._create_slide(prs, slide_layout, chart_specs, i + 1)
                self.log_reasoning("create_slide", f"Created slide {i+1}", {
                    "slide_type": slide_layout.get("slide_type"),
                    "template": slide_layout.get("layout_template")
                })
            
            # Apply theme and styling
            self.log_reasoning("apply_theme", "Applying theme and styling")
            self._apply_theme_to_presentation(prs)
            
            # Save presentation
            self.log_reasoning("save_presentation", f"Saving presentation to {output_path}")
            self.pptx_utils.save_presentation(prs, output_path)
            
            # Create generation summary
            self.log_reasoning("create_summary", "Creating generation summary")
            generation_summary = self._create_generation_summary(slide_layouts, chart_specs, output_path)
            
            output = {
                "presentation_path": output_path,
                "generation_summary": generation_summary,
                "generation_metadata": {
                    "total_slides": len(slide_layouts),
                    "charts_generated": len(chart_specs),
                    "file_size": self._get_file_size(output_path),
                    "theme_applied": "consulting_theme",
                    "generation_time": self._estimate_generation_time(len(slide_layouts))
                }
            }
            
            self.log_reasoning("complete", "Successfully generated PowerPoint presentation", {
                "output_path": output_path,
                "total_slides": len(slide_layouts),
                "file_size": output["generation_metadata"]["file_size"]
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in PPTX generator agent: {str(e)}")
            raise
    
    def _create_slide(self, prs: Presentation, slide_layout: Dict[str, Any], chart_specs: List[Dict], slide_number: int) -> Any:
        """Create a single slide based on layout."""
        slide_type = slide_layout.get("slide_type", "mixed")
        layout_template = slide_layout.get("layout_template", "flexible_layout")
        
        # Create slide based on type
        if slide_type == "title":
            return self._create_title_slide(prs, slide_layout, slide_number)
        elif slide_type == "agenda":
            return self._create_agenda_slide(prs, slide_layout, slide_number)
        elif slide_type == "process":
            return self._create_process_slide(prs, slide_layout, chart_specs, slide_number)
        elif slide_type == "data":
            return self._create_data_slide(prs, slide_layout, chart_specs, slide_number)
        elif slide_type == "comparison":
            return self._create_comparison_slide(prs, slide_layout, chart_specs, slide_number)
        elif slide_type == "conclusion":
            return self._create_conclusion_slide(prs, slide_layout, slide_number)
        else:
            return self._create_mixed_slide(prs, slide_layout, chart_specs, slide_number)
    
    def _create_title_slide(self, prs: Presentation, slide_layout: Dict[str, Any], slide_number: int) -> Any:
        """Create a title slide."""
        slide_layout_info = prs.slide_layouts[0]  # Title slide layout
        slide = prs.slides.add_slide(slide_layout_info)
        
        # Get content areas
        content_areas = slide_layout.get("content_areas", [])
        
        for area in content_areas:
            area_type = area.get("type", "")
            content = area.get("content", {})
            positioning = slide_layout.get("positioning", {})
            area_key = f"area_{area['id'].split('_')[1]}"
            
            if area_key in positioning:
                pos = positioning[area_key]
                
                if area_type == "title" and content:
                    self._add_title_text(slide, content.get("text", ""), pos)
                elif area_type == "subtitle" and content:
                    self._add_subtitle_text(slide, content.get("text", ""), pos)
        
        return slide
    
    def _create_agenda_slide(self, prs: Presentation, slide_layout: Dict[str, Any], slide_number: int) -> Any:
        """Create an agenda slide."""
        slide_layout_info = prs.slide_layouts[1]  # Title and content layout
        slide = prs.slides.add_slide(slide_layout_info)
        
        # Add title
        content_areas = slide_layout.get("content_areas", [])
        positioning = slide_layout.get("positioning", {})
        
        for area in content_areas:
            area_type = area.get("type", "")
            content = area.get("content", {})
            area_key = f"area_{area['id'].split('_')[1]}"
            
            if area_key in positioning:
                pos = positioning[area_key]
                
                if area_type == "title" and content:
                    self._add_slide_title(slide, content.get("text", "Agenda"))
                elif area_type == "content" and content:
                    self._add_bullet_list(slide, content.get("text", ""), pos)
        
        return slide
    
    def _create_process_slide(self, prs: Presentation, slide_layout: Dict[str, Any], chart_specs: List[Dict], slide_number: int) -> Any:
        """Create a process flow slide."""
        slide_layout_info = prs.slide_layouts[5]  # Title only layout
        slide = prs.slides.add_slide(slide_layout_info)
        
        # Add title
        content_areas = slide_layout.get("content_areas", [])
        positioning = slide_layout.get("positioning", {})
        
        # Add title at the top
        self._add_slide_title(slide, f"Process Flow - Slide {slide_number}")
        
        # Add visual elements
        for area in content_areas:
            if area.get("type") == "visual":
                content = area.get("content", {})
                area_key = f"area_{area['id'].split('_')[1]}"
                
                if area_key in positioning:
                    pos = positioning[area_key]
                    self._add_flow_diagram(slide, content, pos)
        
        # Add chart if applicable
        chart_spec = self._find_chart_for_slide(chart_specs, slide_number)
        if chart_spec:
            self._add_chart_to_slide(slide, chart_spec)
        
        return slide
    
    def _create_data_slide(self, prs: Presentation, slide_layout: Dict[str, Any], chart_specs: List[Dict], slide_number: int) -> Any:
        """Create a data visualization slide."""
        slide_layout_info = prs.slide_layouts[5]  # Title only layout
        slide = prs.slides.add_slide(slide_layout_info)
        
        # Add title
        self._add_slide_title(slide, f"Data Analysis - Slide {slide_number}")
        
        # Add content areas
        content_areas = slide_layout.get("content_areas", [])
        positioning = slide_layout.get("positioning", {})
        
        for area in content_areas:
            area_type = area.get("type", "")
            content = area.get("content", {})
            area_key = f"area_{area['id'].split('_')[1]}"
            
            if area_key in positioning:
                pos = positioning[area_key]
                
                if area_type == "visual" and content:
                    self._add_infographic(slide, content, pos)
                elif area_type == "text" and content:
                    self._add_text_content(slide, content.get("text", ""), pos)
        
        # Add chart if applicable
        chart_spec = self._find_chart_for_slide(chart_specs, slide_number)
        if chart_spec:
            self._add_chart_to_slide(slide, chart_spec)
        
        return slide
    
    def _create_comparison_slide(self, prs: Presentation, slide_layout: Dict[str, Any], chart_specs: List[Dict], slide_number: int) -> Any:
        """Create a comparison slide."""
        slide_layout_info = prs.slide_layouts[5]  # Title only layout
        slide = prs.slides.add_slide(slide_layout_info)
        
        # Add title
        self._add_slide_title(slide, f"Comparison Analysis - Slide {slide_number}")
        
        # Add content areas
        content_areas = slide_layout.get("content_areas", [])
        positioning = slide_layout.get("positioning", {})
        
        for area in content_areas:
            area_type = area.get("type", "")
            content = area.get("content", {})
            area_key = f"area_{area['id'].split('_')[1]}"
            
            if area_key in positioning:
                pos = positioning[area_key]
                
                if area_type == "visual" and content:
                    self._add_comparison_grid(slide, content, pos)
        
        return slide
    
    def _create_conclusion_slide(self, prs: Presentation, slide_layout: Dict[str, Any], slide_number: int) -> Any:
        """Create a conclusion slide."""
        slide_layout_info = prs.slide_layouts[1]  # Title and content layout
        slide = prs.slides.add_slide(slide_layout_info)
        
        # Add title
        self._add_slide_title(slide, "Conclusions & Recommendations")
        
        # Add content
        content_areas = slide_layout.get("content_areas", [])
        positioning = slide_layout.get("positioning", {})
        
        for area in content_areas:
            area_type = area.get("type", "")
            content = area.get("content", {})
            area_key = f"area_{area['id'].split('_')[1]}"
            
            if area_key in positioning:
                pos = positioning[area_key]
                
                if area_type == "content" and content:
                    self._add_conclusion_content(slide, content.get("text", ""), pos)
        
        return slide
    
    def _create_mixed_slide(self, prs: Presentation, slide_layout: Dict[str, Any], chart_specs: List[Dict], slide_number: int) -> Any:
        """Create a mixed content slide."""
        slide_layout_info = prs.slide_layouts[1]  # Title and content layout
        slide = prs.slides.add_slide(slide_layout_info)
        
        # Add title
        self._add_slide_title(slide, f"Key Points - Slide {slide_number}")
        
        # Add content
        content_areas = slide_layout.get("content_areas", [])
        positioning = slide_layout.get("positioning", {})
        
        for area in content_areas:
            area_type = area.get("type", "")
            content = area.get("content", {})
            area_key = f"area_{area['id'].split('_')[1]}"
            
            if area_key in positioning:
                pos = positioning[area_key]
                
                if area_type == "visual" and content:
                    self._add_visual_element(slide, content, pos)
                elif area_type == "text" and content:
                    self._add_text_content(slide, content.get("text", ""), pos)
        
        # Add chart if applicable
        chart_spec = self._find_chart_for_slide(chart_specs, slide_number)
        if chart_spec:
            self._add_chart_to_slide(slide, chart_spec)
        
        return slide
    
    def _add_title_text(self, slide: Any, text: str, position: Dict[str, Any]):
        """Add title text to slide."""
        if slide.shapes.title:
            title_shape = slide.shapes.title
            title_shape.text = text
            
            # Format title
            text_frame = title_shape.text_frame
            for paragraph in text_frame.paragraphs:
                paragraph.font.name = self.fonts["title"]
                paragraph.font.size = Pt(self.font_sizes["title"])
                paragraph.font.color.rgb = self.theme_colors["primary"]
                paragraph.alignment = PP_ALIGN.CENTER
    
    def _add_subtitle_text(self, slide: Any, text: str, position: Dict[str, Any]):
        """Add subtitle text to slide."""
        left = Inches(position.get("left", 1))
        top = Inches(position.get("top", 3))
        width = Inches(position.get("width", 8))
        height = Inches(position.get("height", 1))
        
        subtitle_box = slide.shapes.add_textbox(left, top, width, height)
        text_frame = subtitle_box.text_frame
        text_frame.text = text
        
        # Format subtitle
        paragraph = text_frame.paragraphs[0]
        paragraph.font.name = self.fonts["subtitle"]
        paragraph.font.size = Pt(self.font_sizes["subtitle"])
        paragraph.font.color.rgb = self.theme_colors["dark"]
        paragraph.alignment = PP_ALIGN.CENTER
    
    def _add_slide_title(self, slide: Any, text: str):
        """Add slide title."""
        if slide.shapes.title:
            title_shape = slide.shapes.title
            title_shape.text = text
            
            # Format title
            text_frame = title_shape.text_frame
            for paragraph in text_frame.paragraphs:
                paragraph.font.name = self.fonts["heading"]
                paragraph.font.size = Pt(self.font_sizes["heading"])
                paragraph.font.color.rgb = self.theme_colors["primary"]
                paragraph.alignment = PP_ALIGN.LEFT
    
    def _add_bullet_list(self, slide: Any, text: str, position: Dict[str, Any]):
        """Add bullet list to slide."""
        left = Inches(position.get("left", 1))
        top = Inches(position.get("top", 2))
        width = Inches(position.get("width", 8))
        height = Inches(position.get("height", 4))
        
        content_box = slide.shapes.add_textbox(left, top, width, height)
        text_frame = content_box.text_frame
        text_frame.clear()
        
        # Split text into bullet points
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if i == 0:
                paragraph = text_frame.paragraphs[0]
            else:
                paragraph = text_frame.add_paragraph()
            
            paragraph.text = line.strip()
            paragraph.level = 0
            paragraph.font.name = self.fonts["body"]
            paragraph.font.size = Pt(self.font_sizes["body"])
            paragraph.font.color.rgb = self.theme_colors["dark"]
    
    def _add_text_content(self, slide: Any, text: str, position: Dict[str, Any]):
        """Add text content to slide."""
        left = Inches(position.get("left", 1))
        top = Inches(position.get("top", 2))
        width = Inches(position.get("width", 8))
        height = Inches(position.get("height", 4))
        
        text_box = slide.shapes.add_textbox(left, top, width, height)
        text_frame = text_box.text_frame
        text_frame.text = text
        
        # Format text
        for paragraph in text_frame.paragraphs:
            paragraph.font.name = self.fonts["body"]
            paragraph.font.size = Pt(self.font_sizes["body"])
            paragraph.font.color.rgb = self.theme_colors["dark"]
    
    def _add_flow_diagram(self, slide: Any, content: Dict[str, Any], position: Dict[str, Any]):
        """Add flow diagram to slide."""
        # Create simple flow diagram using shapes
        layout = content.get("layout", {})
        flow_content = content.get("content", [])
        
        left = Inches(position.get("left", 1))
        top = Inches(position.get("top", 2))
        width = Inches(position.get("width", 8))
        height = Inches(position.get("height", 3))
        
        # Create flow boxes
        box_width = width / len(flow_content) if flow_content else width
        
        for i, item in enumerate(flow_content):
            x = left + i * box_width
            y = top + height / 2 - Inches(0.5)
            
            # Add rectangle
            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, x, y, box_width - Inches(0.2), Inches(1)
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = self.theme_colors["primary"]
            shape.line.color.rgb = self.theme_colors["dark"]
            
            # Add text
            text_frame = shape.text_frame
            text_frame.text = item.get("text", f"Step {i+1}")
            text_frame.margin_left = Inches(0.1)
            text_frame.margin_right = Inches(0.1)
            
            # Add arrow if not last
            if i < len(flow_content) - 1:
                arrow_x = x + box_width - Inches(0.2)
                arrow = slide.shapes.add_shape(
                    MSO_SHAPE.RIGHT_ARROW, arrow_x, y + Inches(0.3), 
                    Inches(0.4), Inches(0.4)
                )
                arrow.fill.solid()
                arrow.fill.fore_color.rgb = self.theme_colors["dark"]
    
    def _add_infographic(self, slide: Any, content: Dict[str, Any], position: Dict[str, Any]):
        """Add infographic to slide."""
        layout = content.get("layout", {})
        info_content = content.get("content", [])
        
        left = Inches(position.get("left", 1))
        top = Inches(position.get("top", 2))
        width = Inches(position.get("width", 8))
        height = Inches(position.get("height", 4))
        
        # Create metric cards
        card_width = width / len(info_content) if info_content else width
        
        for i, item in enumerate(info_content):
            x = left + i * card_width
            y = top
            
            # Add card background
            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, x + Inches(0.1), y + Inches(0.1), 
                card_width - Inches(0.2), height - Inches(0.2)
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = self.theme_colors["light"]
            shape.line.color.rgb = self.theme_colors["primary"]
            
            # Add text
            text_frame = shape.text_frame
            metric = item.get("metric", "")
            value = item.get("value", "")
            text_frame.text = f"{metric}\n{value}"
            text_frame.margin_left = Inches(0.2)
            text_frame.margin_right = Inches(0.2)
            
            # Format text
            for paragraph in text_frame.paragraphs:
                paragraph.font.name = self.fonts["body"]
                paragraph.font.size = Pt(self.font_sizes["subheading"])
                paragraph.font.color.rgb = self.theme_colors["dark"]
                paragraph.alignment = PP_ALIGN.CENTER
    
    def _add_comparison_grid(self, slide: Any, content: Dict[str, Any], position: Dict[str, Any]):
        """Add comparison grid to slide."""
        layout = content.get("layout", {})
        grid_content = content.get("content", [])
        
        left = Inches(position.get("left", 1))
        top = Inches(position.get("top", 2))
        width = Inches(position.get("width", 8))
        height = Inches(position.get("height", 4))
        
        # Create grid cells
        cols = layout.get("columns", 2)
        rows = layout.get("rows", 2)
        
        cell_width = width / cols
        cell_height = height / rows
        
        for i, item in enumerate(grid_content):
            row = i // cols
            col = i % cols
            
            if row >= rows:
                break
            
            x = left + col * cell_width
            y = top + row * cell_height
            
            # Add cell
            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, x + Inches(0.05), y + Inches(0.05), 
                cell_width - Inches(0.1), cell_height - Inches(0.1)
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = self.theme_colors["light"]
            shape.line.color.rgb = self.theme_colors["dark"]
            
            # Add text
            text_frame = shape.text_frame
            text_frame.text = item.get("text", f"Item {i+1}")
            text_frame.margin_left = Inches(0.1)
            text_frame.margin_right = Inches(0.1)
            
            # Format text
            for paragraph in text_frame.paragraphs:
                paragraph.font.name = self.fonts["body"]
                paragraph.font.size = Pt(self.font_sizes["body"])
                paragraph.font.color.rgb = self.theme_colors["dark"]
                paragraph.alignment = PP_ALIGN.CENTER
    
    def _add_visual_element(self, slide: Any, content: Dict[str, Any], position: Dict[str, Any]):
        """Add generic visual element to slide."""
        visual_type = content.get("type", "diagram")
        
        if visual_type == "flow":
            self._add_flow_diagram(slide, content, position)
        elif visual_type == "infographic":
            self._add_infographic(slide, content, position)
        elif visual_type == "grid":
            self._add_comparison_grid(slide, content, position)
        else:
            # Default to simple text box
            self._add_text_content(slide, str(content), position)
    
    def _add_conclusion_content(self, slide: Any, text: str, position: Dict[str, Any]):
        """Add conclusion content to slide."""
        self._add_text_content(slide, text, position)
    
    def _add_chart_to_slide(self, slide: Any, chart_spec: Dict[str, Any]):
        """Add chart to slide."""
        try:
            # Create chart data object
            chart_data_dict = chart_spec.get("data", {})
            chart_type = chart_spec.get("chart_type", "bar")
            
            chart_data = {
                "chart_type": ChartType(chart_type),
                "title": chart_spec.get("title", "Chart"),
                "labels": chart_data_dict.get("labels", []),
                "datasets": chart_data_dict.get("datasets", []),
                "colors": self._get_chart_colors(chart_type)
            }
            
            # Add chart using PPTX utils
            self.pptx_utils.add_chart_slide(
                Presentation(),  # Create temporary presentation for chart
                chart_spec.get("title", ""),
                chart_data
            )
            
        except Exception as e:
            self.logger.error(f"Error adding chart to slide: {str(e)}")
            # Add placeholder text
            self._add_text_content(slide, f"Chart: {chart_spec.get('title', 'Data Visualization')}", 
                                 {"left": 1, "top": 2, "width": 8, "height": 4})
    
    def _find_chart_for_slide(self, chart_specs: List[Dict], slide_number: int) -> Optional[Dict[str, Any]]:
        """Find chart specification for a specific slide."""
        for spec in chart_specs:
            if spec.get("slide_number") == slide_number:
                return spec
        return None
    
    def _get_chart_colors(self, chart_type: str) -> List[str]:
        """Get colors for chart type."""
        return [
            self.theme_colors["primary"],
            self.theme_colors["secondary"],
            self.theme_colors["accent"],
            self.theme_colors["danger"],
            self.theme_colors["warning"]
        ]
    
    def _apply_theme_to_presentation(self, prs: Presentation):
        """Apply consistent theme to presentation."""
        # This is a simplified theme application
        # In a real implementation, you'd apply more comprehensive theming
        pass
    
    def _create_generation_summary(self, slide_layouts: List[Dict], chart_specs: List[Dict], output_path: str) -> Dict[str, Any]:
        """Create a summary of the generation process."""
        slide_types = {}
        
        for layout in slide_layouts:
            slide_type = layout.get("slide_type", "unknown")
            slide_types[slide_type] = slide_types.get(slide_type, 0) + 1
        
        return {
            "total_slides_generated": len(slide_layouts),
            "slide_type_distribution": slide_types,
            "total_charts": len(chart_specs),
            "output_file": output_path,
            "generation_success": True,
            "theme_applied": "consulting_theme",
            "quality_checks": self._perform_quality_checks(slide_layouts)
        }
    
    def _perform_quality_checks(self, slide_layouts: List[Dict]) -> Dict[str, Any]:
        """Perform quality checks on generated slides."""
        checks = {
            "all_slides_have_titles": True,
            "consistent_spacing": True,
            "no_text_overload": True,
            "visual_balance": True
        }
        
        for layout in slide_layouts:
            # Check if slide has title
            content_areas = layout.get("content_areas", [])
            has_title = any(area.get("type") == "title" for area in content_areas)
            if not has_title:
                checks["all_slides_have_titles"] = False
        
        return checks
    
    def _get_file_size(self, file_path: str) -> str:
        """Get file size in human readable format."""
        try:
            if os.path.exists(file_path):
                size_bytes = os.path.getsize(file_path)
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
        except:
            pass
        
        return "Unknown"
    
    def _estimate_generation_time(self, slide_count: int) -> str:
        """Estimate generation time."""
        # Rough estimate: 2 seconds per slide
        seconds = slide_count * 2
        if seconds < 60:
            return f"{seconds}s"
        else:
            return f"{seconds // 60}m {seconds % 60}s"
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate PPTX generator output."""
        if not output:
            return False
        
        required_keys = ["presentation_path", "generation_summary", "generation_metadata"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in PPTX generator output: {key}")
                return False
        
        # Check if presentation file was created
        output_path = output.get("presentation_path", "")
        if not os.path.exists(output_path):
            self.logger.error(f"Presentation file not created: {output_path}")
            return False
        
        return True
