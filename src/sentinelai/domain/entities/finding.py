from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sentinelai.domain.entities.severity import Severity


@dataclass(frozen=True)
class Finding:
    title: str
    description: str
    severity: Severity
    location: str
    recommendation: str
    id: UUID = field(default_factory=uuid4)

    def is_critical(self) -> bool:
        return self.severity in (Severity.CRITICAL, Severity.HIGH)
