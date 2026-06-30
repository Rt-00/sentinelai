from sentinelai.domain.ports.llm_port import LLMPort

REPORT_PROMPT = """You are a senior security consultant writing a professional security assessment \
report. Based on the following data, produce a clear, actionable report in Markdown format.

## Source Code Language
{language}

## Code Analysis Findings
{analysis_summary}

## Vulnerability Intelligence
{vuln_summary}

Write the report with these sections:
1. **Executive Summary** — 2-3 sentences for non-technical stakeholders
2. **Critical Findings** — highest severity issues that need immediate attention
3. **Detailed Findings** — all issues with severity, description, location, and remediation
4. **Vulnerability Mapping** — CVE/CWE/OWASP classifications
5. **Remediation Priority** — ordered list of what to fix first and why
6. **Overall Risk Rating** — Critical/High/Medium/Low with justification

Be specific about code locations and provide concrete fix examples."""


class ReportWriter:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    async def write(
        self,
        analysis_summary: str,
        vuln_summary: str,
        language: str,
    ) -> str:
        prompt = REPORT_PROMPT.format(
            language=language,
            analysis_summary=analysis_summary,
            vuln_summary=vuln_summary,
        )

        return await self._llm.invoke(prompt)
