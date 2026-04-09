"""
Data models for the multi-agent system.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class SlideType(str, Enum):
    TITLE = "title"
    SECTION = "section"
    DATA = "data"
    COMPARISON = "comparison"
    PROCESS = "process"
    SUMMARY = "summary"


class ChartType(str, Enum):
    BAR = "bar"
    PIE = "pie"
    LINE = "line"
    AREA = "area"


class MarkdownElement(BaseModel):
    type: str  # heading, paragraph, list, table, code
    content: str
    level: Optional[int] = None  # for headings
    items: Optional[List[str]] = None  # for lists
    headers: Optional[List[str]] = None  # for tables
    rows: Optional[List[List[str]]] = None  # for tables
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ParsedMarkdown(BaseModel):
    title: Optional[str] = None
    elements: List[MarkdownElement]
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Insight(BaseModel):
    text: str
    importance: float  # 0.0 to 1.0
    category: str
    supporting_data: Optional[List[str]] = None


class ExecutiveSummary(BaseModel):
    main_message: str
    key_insights: List[Insight]
    recommendations: List[str]
    metrics: List[Dict[str, Union[str, float]]]


class Storyline(BaseModel):
    narrative_flow: List[str]
    slide_count: int
    content_distribution: Dict[str, int]
    key_themes: List[str]
    structure: List[Dict[str, Any]]


class SlidePlan(BaseModel):
    title: str
    slide_type: SlideType
    key_message: str
    content_blocks: List[Dict[str, Any]]
    visual_elements: List[Dict[str, Any]]
    chart_data: Optional[Dict[str, Any]] = None


class VisualElement(BaseModel):
    type: str  # flow, timeline, grid, diagram
    layout: Dict[str, Any]
    content: List[Dict[str, Any]]
    positioning: Dict[str, Union[int, float]]


class ChartData(BaseModel):
    chart_type: ChartType
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    colors: List[str]


class SlideLayout(BaseModel):
    grid_columns: int
    grid_rows: int
    content_areas: List[Dict[str, Any]]
    spacing: Dict[str, int]
    alignment: str


class Slide(BaseModel):
    plan: SlidePlan
    layout: SlideLayout
    visual_elements: List[VisualElement]
    chart_data: Optional[ChartData] = None
    rendered_content: Optional[Dict[str, Any]] = None


class Presentation(BaseModel):
    title: str
    slides: List[Slide]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    theme: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    agent_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    reasoning: str
    confidence: float
    timestamp: str


class OrchestratorLog(BaseModel):
    step: int
    agent: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    reasoning: str
    success: bool
    errors: Optional[List[str]] = None
