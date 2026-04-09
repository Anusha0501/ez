"""
Markdown parsing utilities.
"""

import re
import logging
from typing import List, Dict, Any, Optional
import markdown
from markdown.extensions import tables, codehilite

from core.models import MarkdownElement, ParsedMarkdown


class MarkdownParser:
    """Parser for converting Markdown to structured data."""
    
    def __init__(self):
        self.logger = logging.getLogger("markdown_parser")
        self.md = markdown.Markdown(extensions=[tables.TableExtension(), codehilite.CodeHiliteExtension()])
    
    def parse(self, markdown_text: str) -> ParsedMarkdown:
        """Parse markdown text into structured format."""
        try:
            self.logger.info("Starting markdown parsing")
            
            # Split into lines
            lines = markdown_text.split('\n')
            elements = []
            sections = []
            current_section = None
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Parse headings
                if line.startswith('#'):
                    element, i = self._parse_heading(lines, i)
                    elements.append(element)
                    
                    # Update section tracking
                    level = element.level
                    if level == 1:
                        current_section = {
                            "title": element.content,
                            "level": level,
                            "start_index": len(elements) - 1,
                            "elements": []
                        }
                        sections.append(current_section)
                    elif current_section:
                        current_section["elements"].append(len(elements) - 1)
                
                # Parse tables
                elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
                    element, i = self._parse_table(lines, i)
                    elements.append(element)
                    if current_section:
                        current_section["elements"].append(len(elements) - 1)
                
                # Parse lists
                elif line.startswith(('-', '*', '+', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    element, i = self._parse_list(lines, i)
                    elements.append(element)
                    if current_section:
                        current_section["elements"].append(len(elements) - 1)
                
                # Parse code blocks
                elif line.startswith('```'):
                    element, i = self._parse_code_block(lines, i)
                    elements.append(element)
                    if current_section:
                        current_section["elements"].append(len(elements) - 1)
                
                # Parse paragraphs
                else:
                    element, i = self._parse_paragraph(lines, i)
                    elements.append(element)
                    if current_section:
                        current_section["elements"].append(len(elements) - 1)
            
            # Extract title from first H1 if available
            title = None
            for element in elements:
                if element.type == "heading" and element.level == 1:
                    title = element.content
                    break
            
            parsed = ParsedMarkdown(
                title=title,
                elements=elements,
                sections=sections,
                metadata={
                    "total_elements": len(elements),
                    "total_sections": len(sections),
                    "has_tables": any(e.type == "table" for e in elements),
                    "has_lists": any(e.type == "list" for e in elements),
                    "has_code": any(e.type == "code" for e in elements)
                }
            )
            
            self.logger.info(f"Successfully parsed markdown: {len(elements)} elements, {len(sections)} sections")
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error parsing markdown: {str(e)}")
            raise
    
    def _parse_heading(self, lines: List[str], start_idx: int) -> tuple[MarkdownElement, int]:
        """Parse a heading line."""
        line = lines[start_idx].strip()
        level = len(line) - len(line.lstrip('#'))
        content = line.lstrip('#').strip()
        
        element = MarkdownElement(
            type="heading",
            content=content,
            level=level,
            metadata={"line_number": start_idx + 1}
        )
        
        return element, start_idx + 1
    
    def _parse_table(self, lines: List[str], start_idx: int) -> tuple[MarkdownElement, int]:
        """Parse a markdown table."""
        table_lines = []
        i = start_idx
        
        while i < len(lines) and '|' in lines[i].strip():
            table_lines.append(lines[i].strip())
            i += 1
        
        # Parse headers
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
        
        # Skip separator line
        if len(table_lines) > 2:
            # Parse rows
            rows = []
            for line in table_lines[2:]:
                if '|' in line:
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    if cells:
                        rows.append(cells)
        else:
            rows = []
        
        element = MarkdownElement(
            type="table",
            content="\\n".join(table_lines),
            headers=headers,
            rows=rows,
            metadata={
                "line_number": start_idx + 1,
                "row_count": len(rows),
                "column_count": len(headers)
            }
        )
        
        return element, i
    
    def _parse_list(self, lines: List[str], start_idx: int) -> tuple[MarkdownElement, int]:
        """Parse a markdown list."""
        items = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Check if it's still a list item
            if line.startswith(('-', '*', '+', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                # Remove list marker
                if line.startswith(('-', '*', '+')):
                    item = line[1:].strip()
                else:
                    # Numbered list
                    item = re.sub(r'^\d+\.\s*', '', line)
                items.append(item)
                i += 1
            else:
                break
        
        element = MarkdownElement(
            type="list",
            content="\\n".join(items),
            items=items,
            metadata={
                "line_number": start_idx + 1,
                "item_count": len(items)
            }
        )
        
        return element, i
    
    def _parse_code_block(self, lines: List[str], start_idx: int) -> tuple[MarkdownElement, int]:
        """Parse a code block."""
        code_lines = []
        i = start_idx + 1  # Skip the opening ```
        
        while i < len(lines) and not lines[i].strip().startswith('```'):
            code_lines.append(lines[i])
            i += 1
        
        element = MarkdownElement(
            type="code",
            content="\\n".join(code_lines),
            metadata={
                "line_number": start_idx + 1,
                "line_count": len(code_lines)
            }
        )
        
        return element, i + 1  # Skip the closing ```
    
    def _parse_paragraph(self, lines: List[str], start_idx: int) -> tuple[MarkdownElement, int]:
        """Parse a paragraph."""
        paragraph_lines = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                break
            
            # Stop if it's a special markdown element
            if (line.startswith('#') or 
                line.startswith('```') or 
                line.startswith(('-', '*', '+')) or
                (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) and line.find('.') < 5) or
                ('|' in line and i + 1 < len(lines) and '|' in lines[i + 1])):
                break
            
            paragraph_lines.append(line)
            i += 1
        
        content = ' '.join(paragraph_lines)
        
        element = MarkdownElement(
            type="paragraph",
            content=content,
            metadata={
                "line_number": start_idx + 1,
                "word_count": len(content.split())
            }
        )
        
        return element, i
    
    def extract_numeric_data(self, parsed: ParsedMarkdown) -> List[Dict[str, Any]]:
        """Extract numeric data from parsed markdown."""
        numeric_data = []
        
        for element in parsed.elements:
            if element.type == "table" and element.rows:
                # Look for numeric data in tables
                for row in element.rows:
                    for i, cell in enumerate(row):
                        # Try to extract numbers
                        numbers = re.findall(r'[-+]?\d*\.?\d+(?:%|,)?', cell)
                        if numbers:
                            numeric_data.append({
                                "type": "table_data",
                                "value": numbers,
                                "context": cell,
                                "row": row,
                                "column_index": i,
                                "column_name": element.headers[i] if element.headers and i < len(element.headers) else f"Column {i+1}"
                            })
            
            elif element.type == "paragraph":
                # Look for numbers in paragraphs
                numbers = re.findall(r'[-+]?\d*\.?\d+(?:%|,)?', element.content)
                if numbers:
                    numeric_data.append({
                        "type": "text_data",
                        "value": numbers,
                        "context": element.content
                    })
        
        return numeric_data
