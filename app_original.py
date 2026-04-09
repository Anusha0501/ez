"""
Streamlit app for Markdown to PPTX conversion using multi-agent AI system.
"""

import streamlit as st
import os
import tempfile
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Import existing multi-agent system
from core.fault_tolerant_orchestrator import FaultTolerantOrchestrator
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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_app")

# Initialize session state
if 'agent_logs' not in st.session_state:
    st.session_state.agent_logs = []
if 'processing_state' not in st.session_state:
    st.session_state.processing_state = 'idle'
if 'pptx_path' not in st.session_state:
    st.session_state.pptx_path = None

def initialize_agents() -> Dict[str, Any]:
    """Initialize all agents with Gemini client."""
    try:
        gemini_client = GeminiClient()
        
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
    except Exception as e:
        st.error(f"Failed to initialize agents: {str(e)}")
        return {}

def generate_ppt_from_markdown(file_content: str, slide_count: int = 12) -> Tuple[Optional[str], List[Dict]]:
    """Generate PPTX from markdown using multi-agent system."""
    try:
        # Initialize agents
        agents = initialize_agents()
        if not agents:
            return None, []
        
        # Initialize fault-tolerant orchestrator
        orchestrator = FaultTolerantOrchestrator(agents)
        
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp_file:
            # Prepare input data
            input_data = {
                "markdown_content": file_content,
                "output_path": tmp_file.name,
                "slide_count": slide_count
            }
            
            # Execute multi-agent workflow
            presentation = orchestrator.execute_workflow_robust(input_data)
            
            # Get execution logs
            agent_logs = orchestrator.get_execution_logs()
            
            return tmp_file.name, agent_logs
            
    except Exception as e:
        st.error(f"Error generating PPTX: {str(e)}")
        logger.error(f"PPTX generation failed: {str(e)}")
        return None, []

def validate_markdown_file(uploaded_file) -> bool:
    """Validate uploaded markdown file."""
    if uploaded_file is None:
        return False
    
    # Check file extension
    if not uploaded_file.name.endswith(('.md', '.markdown')):
        st.error("Please upload a Markdown file (.md or .markdown)")
        return False
    
    # Check file size (max 10MB)
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("File size must be less than 10MB")
        return False
    
    return True

def display_agent_logs(logs: List[Dict]):
    """Display agent execution logs in expandable format."""
    if not logs:
        st.info("No agent logs available")
        return
    
    with st.expander("🤖 Agent Execution Logs", expanded=False):
        for i, log in enumerate(logs):
            agent_name = log.get('agent', 'Unknown')
            timestamp = log.get('timestamp', '')
            action = log.get('action', '')
            details = log.get('details', '')
            
            # Create log entry
            with st.container():
                cols = st.columns([2, 8])
                with cols[0]:
                    st.write(f"**{agent_name}**")
                    st.caption(f"_{timestamp}_")
                
                with cols[1]:
                    if action == 'start':
                        st.success(f"🚀 {action}")
                    elif action == 'complete':
                        st.success(f"✅ {action}")
                    elif action == 'error':
                        st.error(f"❌ {action}")
                    else:
                        st.info(f"📝 {action}")
                    
                    if details:
                        st.json(details)

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Markdown → PPTX Agentic Generator",
        page_icon="🧠",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🧠 Markdown → PPTX Agentic Generator")
    st.markdown("*AI-powered multi-agent system for professional presentations*")
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Slide count control
        slide_count = st.slider(
            "📊 Slide Count",
            min_value=10,
            max_value=15,
            value=12,
            help="Number of slides to generate (10-15 recommended)"
        )
        
        st.markdown("---")
        
        # API Key status
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            st.success("✅ Gemini API Key configured")
        else:
            st.error("❌ Gemini API Key not found")
            st.info("Set GEMINI_API_KEY environment variable")
    
    # Main content area
    st.header("📁 File Upload")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Markdown File",
        type=['md', 'markdown'],
        help="Upload a .md or .markdown file to convert to PowerPoint"
    )
    
    if uploaded_file and validate_markdown_file(uploaded_file):
        # Display file info
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Read file content
        try:
            content = uploaded_file.read().decode('utf-8')
            st.info(f"📄 File size: {len(content):,} characters")
            
            # Generate button
            if st.button("🚀 Generate PPTX", type="primary", use_container_width=True):
                # Update processing state
                st.session_state.processing_state = 'processing'
                
                # Show processing
                with st.spinner("🤖 Running AI agents..."):
                    # Generate PPTX
                    pptx_path, agent_logs = generate_ppt_from_markdown(content, slide_count)
                
                if pptx_path:
                    # Success
                    st.session_state.processing_state = 'complete'
                    st.session_state.pptx_path = pptx_path
                    st.session_state.agent_logs = agent_logs
                    
                    # Display success message
                    st.success("✅ PPTX generated successfully!")
                    st.balloons()
                else:
                    # Error
                    st.session_state.processing_state = 'error'
                    st.error("❌ Failed to generate PPTX")
                    
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
    
    # Display results
    if st.session_state.processing_state == 'complete':
        st.header("📊 Results")
        
        # Success metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", "✅ Complete")
        with col2:
            st.metric("Slides Generated", slide_count)
        
        # Download section
        st.subheader("💾 Download")
        st.success(f"PowerPoint file ready: `{os.path.basename(st.session_state.pptx_path)}`")
        
        # Download button
        with open(st.session_state.pptx_path, 'rb') as f:
            st.download_button(
                label="📥 Download PPTX",
                data=f,
                file_name=os.path.basename(st.session_state.pptx_path),
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        
        # Agent logs
        if st.session_state.agent_logs:
            display_agent_logs(st.session_state.agent_logs)
    
    elif st.session_state.processing_state == 'error':
        st.error("❌ Processing failed. Please try again.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🧠 Powered by Multi-Agent AI System • 9 Agents Working Together
        </div>
        """
    )

if __name__ == "__main__":
    main()
