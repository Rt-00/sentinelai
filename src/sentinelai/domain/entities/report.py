from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sentinelai.domain.entities.finding import Finding
from sentinelai.domain.entities.severity import Severity


@dataclass(frozen=True)
class Report:
    scan_id: UUID
    findings: tuple[Finding, ...]
    summary: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.is_critical())

    def findings_by_severity(self, severity: Severity) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == severity)
