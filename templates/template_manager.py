"""
Template manager for handling PowerPoint templates.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .slide_master import SlideMaster


class TemplateManager:
    """Manages PowerPoint templates and slide masters."""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.logger = logging.getLogger("template_manager")
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent
        self.slide_master = SlideMaster()
        
        # Ensure template directory exists
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Load built-in templates
        self._load_builtin_templates()
        
        # Load custom templates
        self._load_custom_templates()
    
    def _load_builtin_templates(self):
        """Load built-in templates."""
        self.logger.info("Loading built-in templates")
        
        # Built-in templates are defined in SlideMaster
        self.builtin_templates = self.slide_master.list_available_templates()
        self.logger.info(f"Loaded {len(self.builtin_templates)} built-in templates")
    
    def _load_custom_templates(self):
        """Load custom templates from directory."""
        self.custom_templates = {}
        
        template_files = list(self.template_dir.glob("*.json"))
        for template_file in template_files:
            try:
                template = self.slide_master.import_template(str(template_file))
                if template:
                    template_name = template["name"]
                    self.custom_templates[template_name] = template
                    self.logger.info(f"Loaded custom template: {template_name}")
            except Exception as e:
                self.logger.error(f"Failed to load template {template_file}: {str(e)}")
        
        self.logger.info(f"Loaded {len(self.custom_templates)} custom templates")
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name."""
        # Check built-in templates first
        if template_name in self.builtin_templates:
            return self.slide_master.get_layout_specification(template_name)
        
        # Check custom templates
        if template_name in self.custom_templates:
            return self.custom_templates[template_name]
        
        return None
    
    def list_templates(self) -> Dict[str, List[str]]:
        """List all available templates."""
        return {
            "builtin": self.builtin_templates.copy(),
            "custom": list(self.custom_templates.keys())
        }
    
    def create_template(self, name: str, specifications: Dict[str, Any]) -> bool:
        """Create a new custom template."""
        try:
            template = self.slide_master.create_custom_template(name, specifications)
            
            # Save to file
            template_path = self.template_dir / f"{name}.json"
            success = self.slide_master.export_template(name, str(template_path))
            
            if success:
                self.custom_templates[name] = template
                self.logger.info(f"Created custom template: {name}")
                return True
            else:
                self.logger.error(f"Failed to save template: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating template {name}: {str(e)}")
            return False
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a custom template."""
        if template_name in self.builtin_templates:
            self.logger.warning(f"Cannot delete built-in template: {template_name}")
            return False
        
        if template_name not in self.custom_templates:
            self.logger.warning(f"Template not found: {template_name}")
            return False
        
        try:
            # Delete file
            template_path = self.template_dir / f"{template_name}.json"
            if template_path.exists():
                template_path.unlink()
            
            # Remove from memory
            del self.custom_templates[template_name]
            self.logger.info(f"Deleted custom template: {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting template {template_name}: {str(e)}")
            return False
    
    def apply_template_to_presentation(self, presentation, template_name: str) -> bool:
        """Apply a template to a presentation."""
        template = self.get_template(template_name)
        if not template:
            self.logger.error(f"Template not found: {template_name}")
            return False
        
        try:
            # Apply template specifications
            placeholders = template.get("placeholders", {})
            background = template.get("background")
            
            # This is a simplified template application
            # In a real implementation, you'd modify slide masters, layouts, etc.
            self.logger.info(f"Applied template: {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying template {template_name}: {str(e)}")
            return False
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template."""
        template = self.get_template(template_name)
        if not template:
            return None
        
        return {
            "name": template.get("name", template_name),
            "description": template.get("description", ""),
            "type": "builtin" if template_name in self.builtin_templates else "custom",
            "placeholders": list(template.get("placeholders", {}).keys()),
            "background": str(template.get("background", ""))
        }
    
    def export_template(self, template_name: str, output_path: str) -> bool:
        """Export a template to a file."""
        template = self.get_template(template_name)
        if not template:
            self.logger.error(f"Template not found: {template_name}")
            return False
        
        try:
            with open(output_path, 'w') as f:
                json.dump(template, f, indent=2, default=str)
            
            self.logger.info(f"Exported template: {template_name} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting template {template_name}: {str(e)}")
            return False
    
    def import_template(self, template_path: str) -> Optional[str]:
        """Import a template from a file."""
        try:
            template = self.slide_master.import_template(template_path)
            if template:
                template_name = template["name"]
                
                # Save to templates directory
                dest_path = self.template_dir / f"{template_name}.json"
                with open(dest_path, 'w') as f:
                    json.dump(template, f, indent=2, default=str)
                
                self.custom_templates[template_name] = template
                self.logger.info(f"Imported template: {template_name} from {template_path}")
                return template_name
            else:
                self.logger.error(f"Invalid template file: {template_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error importing template from {template_path}: {str(e)}")
            return None
    
    def validate_template(self, template: Dict[str, Any]) -> bool:
        """Validate template structure."""
        required_keys = ["name", "placeholders", "background"]
        
        if not all(key in template for key in required_keys):
            return False
        
        placeholders = template.get("placeholders", {})
        if not isinstance(placeholders, dict):
            return False
        
        # Validate each placeholder
        for placeholder_name, placeholder_spec in placeholders.items():
            if not isinstance(placeholder_spec, dict):
                return False
            
            required_placeholder_keys = ["position", "size"]
            if not all(key in placeholder_spec for key in required_placeholder_keys):
                return False
        
        return True
    
    def get_slide_master(self) -> SlideMaster:
        """Get the slide master instance."""
        return self.slide_master
    
    def refresh_templates(self):
        """Refresh templates from disk."""
        self.logger.info("Refreshing templates")
        self._load_custom_templates()
    
    def get_template_usage_stats(self) -> Dict[str, Any]:
        """Get template usage statistics."""
        # This would typically track template usage over time
        # For now, return basic info
        return {
            "total_builtin": len(self.builtin_templates),
            "total_custom": len(self.custom_templates),
            "total_available": len(self.builtin_templates) + len(self.custom_templates),
            "template_directory": str(self.template_dir)
        }
