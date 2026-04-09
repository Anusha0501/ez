"""
Parser Agent - Converts Markdown to structured JSON.
"""

import json
import logging
from typing import Dict, Any

from ..core.agent import BaseAgent
from ..core.models import ParsedMarkdown
from ..utils.markdown_parser import MarkdownParser


class ParserAgent(BaseAgent):
    """Agent responsible for parsing Markdown into structured data."""
    
    def __init__(self):
        super().__init__("parser_agent")
        self.markdown_parser = MarkdownParser()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process markdown content into structured format."""
        try:
            self.log_reasoning("start", "Starting markdown parsing")
            
            markdown_content = input_data.get("markdown_content", "")
            if not markdown_content:
                raise ValueError("No markdown content provided")
            
            self.log_reasoning("parse", "Parsing markdown content", {
                "content_length": len(markdown_content),
                "line_count": len(markdown_content.split('\n'))
            })
            
            # Parse the markdown
            parsed_data = self.markdown_parser.parse(markdown_content)
            
            # Extract numeric data
            self.log_reasoning("extract_numeric", "Extracting numeric data")
            numeric_data = self.markdown_parser.extract_numeric_data(parsed_data)
            
            # Analyze content structure
            self.log_reasoning("analyze_structure", "Analyzing content structure")
            structure_analysis = self._analyze_structure(parsed_data)
            
            # Prepare output
            output = {
                "parsed_data": parsed_data.dict(),
                "numeric_data": numeric_data,
                "structure_analysis": structure_analysis,
                "parsing_metadata": {
                    "total_elements": len(parsed_data.elements),
                    "total_sections": len(parsed_data.sections),
                    "has_tables": parsed_data.metadata.get("has_tables", False),
                    "has_lists": parsed_data.metadata.get("has_lists", False),
                    "has_code": parsed_data.metadata.get("has_code", False),
                    "numeric_data_points": len(numeric_data)
                }
            }
            
            self.log_reasoning("complete", "Successfully parsed markdown", {
                "elements_found": len(parsed_data.elements),
                "numeric_points": len(numeric_data),
                "sections_found": len(parsed_data.sections)
            })
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error in parser agent: {str(e)}")
            raise
    
    def _analyze_structure(self, parsed_data: ParsedMarkdown) -> Dict[str, Any]:
        """Analyze the structure of the parsed markdown."""
        analysis = {
            "content_density": {},
            "heading_hierarchy": {},
            "content_types": {},
            "readability_metrics": {}
        }
        
        # Analyze content density by section
        for section in parsed_data.sections:
            section_name = section["title"]
            element_count = len(section["elements"])
            analysis["content_density"][section_name] = element_count
        
        # Analyze heading hierarchy
        heading_levels = {}
        for element in parsed_data.elements:
            if element.type == "heading":
                level = element.level
                heading_levels[level] = heading_levels.get(level, 0) + 1
        
        analysis["heading_hierarchy"] = {
            f"h{level}": count for level, count in heading_levels.items()
        }
        
        # Analyze content types
        content_types = {}
        for element in parsed_data.elements:
            content_type = element.type
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        analysis["content_types"] = content_types
        
        # Calculate readability metrics
        total_words = 0
        total_sentences = 0
        
        for element in parsed_data.elements:
            if element.type in ["paragraph", "heading"]:
                text = element.content
                words = len(text.split())
                sentences = len(text.split('.'))
                
                total_words += words
                total_sentences += sentences
        
        avg_words_per_sentence = total_words / total_sentences if total_sentences > 0 else 0
        
        analysis["readability_metrics"] = {
            "total_words": total_words,
            "total_sentences": total_sentences,
            "avg_words_per_sentence": round(avg_words_per_sentence, 2)
        }
        
        return analysis
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the parser output."""
        if not output:
            return False
        
        required_keys = ["parsed_data", "numeric_data", "structure_analysis", "parsing_metadata"]
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key in parser output: {key}")
                return False
        
        # Validate parsed_data structure
        parsed_data = output.get("parsed_data", {})
        if not isinstance(parsed_data, dict):
            self.logger.error("parsed_data is not a dictionary")
            return False
        
        required_parsed_keys = ["elements", "sections"]
        for key in required_parsed_keys:
            if key not in parsed_data:
                self.logger.error(f"Missing required key in parsed_data: {key}")
                return False
        
        return True
