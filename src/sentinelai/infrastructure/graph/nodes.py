from langchain_core.messages import AIMessage, SystemMessage

from sentinelai.application.services.code_analyzer import CodeAnalyzer
from sentinelai.application.services.vuln_scanner import VulnScanner
from sentinelai.application.services.report_writer import ReportWriter
from sentinelai.domain.ports.llm_port import LLMPort
from sentinelai.infrastructure.graph.state import (
    AgentState,
    SupervisorDecision,
    VulnMatch,
)


SUPERVISOR_PROMPT = """You are the Supervisor of a security analysis system. You coordinate three \
specialist agents:

1. **code_analyzer** — Analyzes source code for security vulnerabilities
2. **vuln_scanner** — Maps findings to known CVEs and vulnerability databases
3. **report_writer** — Produces a professional security assessment report

Current state:
- Agents already called: {agents_called}
- Code analysis done: {has_analysis}
- Vulnerability scan done: {has_vulns}
- Report generated: {has_report}

Rules:
- code_analyzer MUST run first (needs source code)
- vuln_scanner MUST run after code_analyzer (needs findings)
- report_writer MUST run after both code_analyzer AND vuln_scanner
- Each agent should only run ONCE
- When report_writer is done, return FINISH

Decide which agent to call next, or FINISH if the workflow is complete."""


class GraphNodes:
    """Encapsulates all graph nodes with their dependencies."""

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm
        self._code_analyzer = CodeAnalyzer(llm=llm)
        self._vuln_scanner = VulnScanner(llm=llm)
        self._report_writer = ReportWriter(llm=llm)

    async def intake(self, state: AgentState) -> dict:
        """Validates input and prepares the scan."""
        if not state.scan_input:
            return {
                "status": "error",
                "error": "No scan input provided",
                "messages": [AIMessage(content="Error: no source code provided for analysis.")],
            }

        return {
            "status": "routing",
            "messages": [
                SystemMessage(
                    content=f"Scan intake complete. Language: {state.scan_input.language}. "
                    f"Routing to Supervisor."
                ),
            ],
        }

    async def supervisor(self, state: AgentState) -> dict:
        """Decides which agent to call next based on current state."""
        if state.status == "error":
            return {
                "current_agent": "FINISH",
                "messages": [AIMessage(content=f"Aborting due to error: {state.error}")],
            }

        prompt = SUPERVISOR_PROMPT.format(
            agents_called=", ".join(state.agents_called) or "none",
            has_analysis=state.analysis is not None,
            has_vulns=len(state.vuln_matches) > 0,
            has_report=bool(state.report),
        )

        decision = await self._llm.invoke_structured(prompt, SupervisorDecision)
        assert isinstance(decision, SupervisorDecision)

        return {
            "current_agent": decision.next_agent,
            "messages": [
                SystemMessage(
                    content=f"Supervisor decision: route to {decision.next_agent}. "
                    f"Reason: {decision.reasoning}"
                ),
            ],
        }

    async def analyze_code(self, state: AgentState) -> dict:
        """Runs the Code Analyzer on the source code."""
        scan_input = state.scan_input
        if not scan_input:
            return {"status": "error", "error": "Missing scan input in analyze_code"}

        try:
            analysis = await self._code_analyzer.analyze(
                source_code=scan_input.source_code,
                language=scan_input.language,
                context=scan_input.context,
            )

            findings = CodeAnalyzer.to_domain_findings(analysis)
            critical = sum(1 for f in findings if f.is_critical())

            return {
                "analysis": analysis,
                "agents_called": state.agents_called + ["code_analyzer"],
                "status": "routing",
                "messages": [
                    AIMessage(
                        content=f"Code analysis complete: {len(findings)} findings "
                        f"({critical} critical/high)."
                    ),
                ],
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "messages": [AIMessage(content=f"Code analysis failed: {e}")],
            }

    async def scan_vulns(self, state: AgentState) -> dict:
        """Maps findings to known CVEs and vulnerability patterns."""
        if not state.analysis:
            return {"status": "error", "error": "No analysis data for vuln scanning"}

        try:
            findings_summary = "\n".join(
                f"- [{f.severity.upper()}] {f.title}: {f.description}"
                for f in state.analysis.findings
            )

            language = state.scan_input.language if state.scan_input else "unknown"
            result = await self._vuln_scanner.scan(findings_summary, language)

            vuln_matches = [
                VulnMatch(
                    cve_id=m.cve_id,
                    title=m.title,
                    description=m.description,
                    severity=m.severity,
                    relevance=m.relevance,
                )
                for m in result.matches
            ]

            return {
                "vuln_matches": vuln_matches,
                "agents_called": state.agents_called + ["vuln_scanner"],
                "status": "routing",
                "messages": [
                    AIMessage(
                        content=f"Vulnerability scan complete: {len(vuln_matches)} CVE matches. "
                        f"{result.assessment}"
                    ),
                ],
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "messages": [AIMessage(content=f"Vulnerability scan failed: {e}")],
            }

    async def write_report(self, state: AgentState) -> dict:
        """Generates the final security assessment report."""
        if not state.analysis:
            return {"status": "error", "error": "No analysis data for report"}

        try:
            analysis_summary = "\n".join(
                f"- [{f.severity.upper()}] {f.title}: {f.description} "
                f"(Location: {f.location}, Fix: {f.recommendation})"
                for f in state.analysis.findings
            )

            vuln_summary = (
                "\n".join(
                    f"- {v.cve_id} — {v.title} [{v.severity.upper()}]: {v.relevance}"
                    for v in state.vuln_matches
                )
                or "No specific CVE matches found."
            )

            language = state.scan_input.language if state.scan_input else "unknown"
            report = await self._report_writer.write(analysis_summary, vuln_summary, language)

            return {
                "report": report,
                "agents_called": state.agents_called + ["report_writer"],
                "status": "routing",
                "messages": [AIMessage(content="Security report generated successfully.")],
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "messages": [AIMessage(content=f"Report generation failed: {e}")],
            }
