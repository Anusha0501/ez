#!/usr/bin/env python3
"""
Multi-Agent AI System for Markdown to PowerPoint Conversion
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Import core components
from core.orchestrator import Orchestrator
from core.models import Presentation
from agents import (
    ParserAgent,
    InsightAgent,
    StorylineAgent,
    SlidePlanningAgent,
    SlideClassifierAgent,
    VisualTransformationAgent,
    ChartDecisionAgent,
    LayoutEngine,
    PPTXGeneratorAgent
)
from utils.gemini_client import GeminiClient


def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration. Creates parent directories for the log file."""
    level = logging.DEBUG if verbose else logging.INFO
    log_path = Path(log_file or "logs/md2pptx.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path)
        ]
    )


def create_agents(gemini_client: GeminiClient) -> dict:
    """Create and initialize all agents."""
    return {
        "parser_agent": ParserAgent(),
        "insight_agent": InsightAgent(gemini_client),
        "storyline_agent": StorylineAgent(gemini_client),
        "slide_planning_agent": SlidePlanningAgent(gemini_client),
        "slide_classifier_agent": SlideClassifierAgent(gemini_client),
        "visual_transformation_agent": VisualTransformationAgent(gemini_client),
        "chart_decision_agent": ChartDecisionAgent(gemini_client),
        "layout_engine": LayoutEngine(),
        "pptx_generator_agent": PPTXGeneratorAgent()
    }


def validate_input_file(input_path: str) -> Path:
    """Validate input markdown file."""
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")
    
    if path.suffix.lower() not in ['.md', '.markdown']:
        raise ValueError(f"Input file must be a markdown file (.md or .markdown): {input_path}")
    
    return path


def validate_output_path(output_path: str) -> Path:
    """Validate and prepare output path."""
    path = Path(output_path)
    
    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure .pptx extension
    if path.suffix.lower() != '.pptx':
        path = path.with_suffix('.pptx')
    
    return path


def read_markdown_file(input_path: Path) -> str:
    """Read markdown content from file."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            raise ValueError(f"Input file is empty: {input_path}")
        
        return content
    except UnicodeDecodeError:
        # Try different encodings
        for encoding in ['latin-1', 'cp1252']:
            try:
                with open(input_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Unable to read file with supported encodings: {input_path}")


def create_sample_markdown() -> str:
    """Create a sample markdown file for testing."""
    sample_content = """# Digital Transformation Strategy

## Executive Summary

This presentation outlines our comprehensive digital transformation strategy for 2024-2025. Our approach focuses on three key pillars: technology modernization, process optimization, and cultural change.

## Current State Analysis

### Technology Assessment

- Legacy systems: 65% of infrastructure
- Cloud adoption: 35% of workloads
- Automation level: 20% of processes
- Digital skills gap: 40% of workforce

### Process Analysis

| Process | Current State | Target State | Gap |
|----------|---------------|---------------|-----|
| Customer Onboarding | Manual (5 days) | Automated (1 day) | 80% |
| Invoice Processing | Paper-based | Digital | 100% |
| Reporting | Monthly | Real-time | 95% |

## Strategic Priorities

### 1. Technology Modernization

**Cloud Migration Strategy**
- Migrate 80% of workloads to cloud by Q4 2024
- Implement hybrid architecture for legacy systems
- Adopt microservices architecture for new applications

**Data Infrastructure**
- Implement unified data platform
- Establish data governance framework
- Deploy advanced analytics capabilities

### 2. Process Optimization

**Automation Roadmap**
- Identify high-impact automation opportunities
- Implement RPA for repetitive tasks
- Streamline end-to-end workflows

**Digital Customer Experience**
- Redesign customer journey
- Implement omnichannel support
- Personalize customer interactions

### 3. Cultural Transformation

**Digital Skills Development**
- Upskill 500 employees in digital technologies
- Create digital champion program
- Establish continuous learning culture

**Change Management**
- Communicate transformation vision
- Address resistance to change
- Celebrate quick wins

## Implementation Timeline

### Phase 1: Foundation (Q1-Q2 2024)
- Infrastructure setup
- Team formation
- Pilot projects

### Phase 2: Scale (Q3-Q4 2024)
- Full deployment
- Process optimization
- Skills development

### Phase 3: Optimize (Q1-Q2 2025)
- Performance measurement
- Continuous improvement
- Innovation scaling

## Expected Outcomes

### Financial Impact

- Cost reduction: 25% in operational costs
- Revenue growth: 15% through digital channels
- ROI: 200% within 3 years

### Operational Benefits

- Process efficiency: 60% improvement
- Customer satisfaction: 40% increase
- Employee productivity: 35% boost

### Risk Mitigation

- Cybersecurity enhancement
- Business continuity improvement
- Regulatory compliance assurance

## Next Steps

1. Secure executive sponsorship
2. Allocate budget and resources
3. Establish governance structure
4. Launch pilot programs
5. Monitor and adjust strategy

## Conclusion

Digital transformation is not just about technology—it's about reimagining how we create value for our customers and stakeholders. With clear strategy, strong leadership, and committed execution, we can achieve our vision of becoming a digital-first organization.
"""
    
    return sample_content


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PowerPoint using Multi-Agent AI System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py input.md output.pptx
  python main.py input.md output.pptx --verbose
  python main.py --sample > sample.md
  python main.py input.md output.pptx --template custom.pptx
        """
    )
    
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input markdown file path"
    )
    
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output PowerPoint file path"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--template", "-t",
        help="PowerPoint template file path"
    )
    
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Generate sample markdown file to stdout"
    )
    
    parser.add_argument(
        "--log-file",
        default="logs/md2pptx.log",
        help="Log file path (default: logs/md2pptx.log)"
    )
    
    args = parser.parse_args()
    
    # Setup logging (honors --log-file; ensures log directory exists)
    setup_logging(args.verbose, args.log_file)
    logger = logging.getLogger("main")
    
    # Handle sample generation
    if args.sample:
        print(create_sample_markdown())
        return 0
    
    # Validate arguments
    if not args.input_file or not args.output_file:
        parser.error("Both input_file and output_file are required unless using --sample")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Validate input and output paths
        input_path = validate_input_file(args.input_file)
        output_path = validate_output_path(args.output_file)
        
        logger.info(f"Processing: {input_path} -> {output_path}")
        
        # Read markdown content
        markdown_content = read_markdown_file(input_path)
        logger.info(f"Read {len(markdown_content)} characters from {input_path}")
        
        # Initialize Gemini client
        try:
            gemini_client = GeminiClient()
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            print(f"Error: Failed to initialize Gemini client. Please check your GEMINI_API_KEY environment variable.")
            return 1
        
        # Create agents
        agents = create_agents(gemini_client)
        logger.info("All agents initialized successfully")
        
        # Create orchestrator
        orchestrator = Orchestrator(agents)
        logger.info("Orchestrator initialized")
        
        # Prepare input data
        input_data = {
            "markdown_content": markdown_content,
            "output_path": str(output_path),
            "template_path": args.template
        }
        
        # Execute workflow
        logger.info("Starting multi-agent workflow...")
        presentation = orchestrator.execute_workflow(input_data)
        
        # Save execution log
        log_output_path = output_path.with_suffix('.json')
        orchestrator.save_execution_log(str(log_output_path))
        logger.info(f"Execution log saved to {log_output_path}")
        
        # Print summary
        summary = orchestrator.get_execution_summary()
        print(f"\n✅ Presentation generated successfully!")
        print(f"📁 Output: {output_path}")
        print(f"📊 Total slides: {summary['total_steps']}")
        print(f"✨ Success rate: {summary['success_rate']:.1%}")
        print(f"📝 Execution log: {log_output_path}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"Error: An unexpected error occurred. Check the log file for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
