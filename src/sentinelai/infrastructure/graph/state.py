from typing import Annotated, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from sentinelai.application.services.code_analyzer import AnalysisOutput


class ScanInput(BaseModel):
    source_code: str
    language: str
    context: str = ""


class VulnMatch(BaseModel):
    cve_id: str = ""
    title: str = ""
    description: str = ""
    severity: str = ""
    relevance: str = ""


AgentName = Literal["code_analyzer", "vuln_scanner", "report_writer", "FINISH"]


class SupervisorDecision(BaseModel):
    next_agent: AgentName = Field(description="Which agent to route to next, or FINISH if done")
    reasoning: str = Field(description="Brief explanation of why this agent was chosen")


class AgentState(BaseModel):
    """Central state that flows through all nodes in the graph."""

    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    scan_input: ScanInput | None = None
    analysis: AnalysisOutput | None = None
    vuln_matches: list[VulnMatch] = Field(default_factory=list)
    report: str = ""
    current_agent: str = ""
    agents_called: list[str] = Field(default_factory=list)
    status: str = "pending"
    error: str | None = None
