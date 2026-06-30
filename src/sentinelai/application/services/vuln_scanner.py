from pydantic import BaseModel, Field

from sentinelai.domain.ports.llm_port import LLMPort


class VulnScanOutput(BaseModel):
    matches: list[VulnMatchOutput] = Field(description="List of potential CVE matches")
    assessment: str = Field(description="Overall vulnerability assessment")


class VulnMatchOutput(BaseModel):
    cve_id: str = Field(description="CVE identifier (e.g., CVE-2024-1234) or 'N/A' if general")
    title: str = Field(description="Short title of the vulnerability")
    description: str = Field(description="How this CVE relates to the analyzed code")
    severity: str = Field(description="One of: critical, high, medium, low")
    relevance: str = Field(description="Why this CVE is relevant to the specific code")


# Rebuild model to resolve forward reference
VulnScanOutput.model_rebuild()


VULN_SCAN_PROMPT = """You are a vulnerability intelligence analyst. Map the following security \
findings to known CVEs or vulnerability classes. Be concise.

Language: {language}

Findings:
{findings_summary}

For each finding return: a CVE id (or 'N/A'), a short title, one-line description, severity, \
and one-line relevance. Keep each field under 20 words. Return structured results."""


class VulnScanner:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    async def scan(self, findings_summary: str, language: str) -> VulnScanOutput:
        prompt = VULN_SCAN_PROMPT.format(
            language=language,
            findings_summary=findings_summary,
        )

        result = await self._llm.invoke_structured(prompt, VulnScanOutput)
        assert isinstance(result, VulnScanOutput)

        return result
