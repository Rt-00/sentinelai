from langgraph.graph import END, START, StateGraph

from sentinelai.domain.ports.llm_port import LLMPort
from sentinelai.infrastructure.graph.nodes import GraphNodes
from sentinelai.infrastructure.graph.state import AgentState


def build_graph(llm: LLMPort) -> StateGraph:
    """Builds and compiles the SentinelAI agent graph.

    Phase 2 flow (linear):
        START -> intake -> analyze_code -> synthesize -> END

    Phase 3 will add conditional edges and the Supervisor node.
    """
    nodes = GraphNodes(llm=llm)
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("intake", nodes.intake)
    graph.add_node("analyze_code", nodes.analyze_code)
    graph.add_node("synthesize", nodes.synthesize)

    # Linear edges (Phase 2)
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "analyze_code")
    graph.add_edge("analyze_code", "synthesize")
    graph.add_edge("synthesize", END)

    return graph


def compile_graph(llm: LLMPort):
    """Returns a compiled, runnable graph."""
    graph = build_graph(llm)
    return graph.compile()
