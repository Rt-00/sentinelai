from langchain_core.messages import AIMessage, SystemMessage

from sentinelai.application.services.code_analyzer import CodeAnalyzer
from sentinelai.domain.ports.llm_port import LLMPort
from sentinelai.infrastructure.graph.state import AgentState


class GraphNodes:
    """Encapsulates all graph nodes with their dependencies."""

    def __init__(self, llm: LLMPort) -> None:
        self._code_analyzer = CodeAnalyzer(llm=llm)

    async def intake(self, state: AgentState) -> dict:
        """First Node: validates input and prepares the scan."""
        scan_input = state.scan_input

        if not scan_input:
            return {
                "status": "error",
                "error": "No scan input provided",
                "messages": [AIMessage(content="Error: no source code provided for analysis.")],
            }

        return {
            "current_agent": "code_analyzer",
            "status": "analyzing",
            "messages": [
                SystemMessage(content="Scan intake complete. Routing to Code Analyzer."),
            ],
        }

    async def analyze_code(self, state: AgentState) -> dict:
        """Runs the Code Analyzer chain on the source code."""
        scan_input = state.scan_input

        if not scan_input:
            return {"status": "error", "error": "Missing scan input in the analyze_code node"}

        try:
            analysis = await self._code_analyzer.analyze(
                source_code=scan_input.source_code,
                language=scan_input.language,
                context=scan_input.context,
            )

            findings = CodeAnalyzer.to_domain_findings(analysis)
            critical = sum(1 for f in findings if f.is_critical())

            summary_message = (
                f"Analysis complete: found {len(findings)} issues "
                f"({critical}) critical/high severity."
            )

            return {
                "analysis": analysis,
                "current_agent": "code_analyzer",
                "status": "analyzed",
                "messages": [AIMessage(content=summary_message)],
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "messages": [AIMessage(content=f"Analysis failed: {e}")],
            }

    async def synthesize(self, state: AgentState) -> dict:
        """Final node: produces the formatted output."""
        if state.status == "error":
            return {
                "status": "completed_with_errors",
                "messages": [
                    AIMessage(content=f"Scan finished with errors: {state.error}"),
                ],
            }

        analysis = state.analysis
        if not analysis:
            return {
                "status": "completed_with_errors",
                "messages": [AIMessage(content="No analysis data to synthesize.")],
            }

        findings = CodeAnalyzer.to_domain_findings(analysis)
        lines = ["## Security Scan Report\n", f"**Summary:** {analysis.summary}\n"]

        for finding in findings:
            icon = "🔴" if finding.is_critical() else "🟡"
            lines.append(f"{icon} **[{finding.severity.value.upper()}] {finding.title}**")
            lines.append(f"   Location: {finding.location}")
            lines.append(f"   {finding.description}")
            lines.append(f"   **Fix:** {finding.recommendation}\n")

        report = "\n".join(lines)

        return {
            "status": "completed",
            "messages": [AIMessage(content=report)],
        }
