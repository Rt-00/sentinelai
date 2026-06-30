from langgraph.graph import StateGraph, START, END

from sentinelai.domain.ports.llm_port import LLMPort
from sentinelai.infrastructure.graph.nodes import GraphNodes
from sentinelai.infrastructure.graph.state import AgentState


def route_from_supervisor(state: AgentState) -> str:
    """Conditional edge: routes based on the Supervisor's decision."""
    match state.current_agent:
        case "code_analyzer":
            return "analyze_code"
        case "vuln_scanner":
            return "scan_vulns"
        case "report_writer":
            return "write_report"
        case "FINISH":
            return "finalize"
        case _:
            return "finalize"


def build_graph(llm: LLMPort) -> StateGraph:
    """Builds the SentinelAI multi-agent graph with Supervisor routing.

    Flow:
        START → intake → supervisor ←──────────────────┐
                            │                          │
                            ├── code_analyzer ─────────┤
                            ├── vuln_scanner ──────────┤
                            ├── report_writer ─────────┘
                            └── FINISH → finalize → END
    """
    nodes = GraphNodes(llm=llm)

    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("intake", nodes.intake)
    graph.add_node("supervisor", nodes.supervisor)
    graph.add_node("analyze_code", nodes.analyze_code)
    graph.add_node("scan_vulns", nodes.scan_vulns)
    graph.add_node("write_report", nodes.write_report)
    graph.add_node("finalize", _finalize)

    # Entry edge
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "supervisor")

    # Supervisor routes conditionally
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "analyze_code": "analyze_code",
            "scan_vulns": "scan_vulns",
            "write_report": "write_report",
            "finalize": "finalize",
        },
    )

    # All agents loop back to supervisor
    graph.add_edge("analyze_code", "supervisor")
    graph.add_edge("scan_vulns", "supervisor")
    graph.add_edge("write_report", "supervisor")

    # Finalize exits
    graph.add_edge("finalize", END)

    return graph


async def _finalize(state: AgentState) -> dict:
    from langchain_core.messages import AIMessage

    if state.report:
        return {
            "status": "completed",
            "messages": [AIMessage(content=state.report)],
        }

    return {
        "status": "completed_with_errors",
        "messages": [AIMessage(content=f"Scan finished. Error: {state.error or 'unknown'}")],
    }


def compile_graph(llm: LLMPort):
    """Returns a compiled, runnable graph."""
    graph = build_graph(llm)
    return graph.compile()
