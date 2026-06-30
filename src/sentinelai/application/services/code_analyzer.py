from pydantic import BaseModel, Field

from sentinelai.domain.entities.finding import Finding
from sentinelai.domain.entities.severity import Severity
from sentinelai.domain.ports.llm_port import LLMPort


class FindingOutput(BaseModel):
    title: str = Field(description="Short title of the security finding")
    description: str = Field(description="Detailed explanation of the vulnerability")
    severity: str = Field(description="One of: critical, high, medium, low, info")
    location: str = Field(description="Where in the code the issue was found")
    recommendation: str = Field(description="How to fix the vulnerability")


class AnalysisOutput(BaseModel):
    findings: list[FindingOutput] = Field(description="List of security findings")
    summary: str = Field(description="Brief overall security assessment")


ANALYSIS_PROMPT = """You are a senior security code reviewer. Analyze the following {language} code \
for security vulnerabilities, focusing on:

- Injection flaws (SQL, command, LDAP)
- Authentication and authorization issues
- Sensitive data exposure
- Security misconfigurations
- Cross-site scripting (XSS)
- Insecure deserialization
- Known vulnerable components
- Insufficient logging

Code to analyze:
```{language}
{source_code}
```

{context}

Return a structured analysis with all findings."""


class CodeAnalyzer:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    async def analyze(self, source_code: str, language: str, context: str = "") -> AnalysisOutput:
        prompt = ANALYSIS_PROMPT.format(
            language=language,
            source_code=source_code,
            context=f"Additional context: {context}" if context else "",
        )

        result = await self._llm.invoke_structured(prompt, AnalysisOutput)
        assert isinstance(result, AnalysisOutput)

        return result

    @staticmethod
    def to_domain_findings(output: AnalysisOutput) -> list[Finding]:
        return [
            Finding(
                title=f.title,
                description=f.description,
                severity=Severity(f.severity.lower()),
                location=f.location,
                recommendation=f.recommendation,
            )
            for f in output.findings
        ]
