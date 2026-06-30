from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from sentinelai.application.services.code_analyzer import AnalysisOutput


class ScanInput(BaseModel):
    source_code: str
    language: str
    context: str = ""


class AgentState(BaseModel):
    """Central state that flows through all nodes in the graph."""

    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    scan_input: ScanInput | None = None
    analysis: AnalysisOutput | None = None
    current_agent: str = ""
    status: str = "pending"
    error: str | None = None
