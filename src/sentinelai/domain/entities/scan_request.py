from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScanRequest:
    source_code: str
    language: str
    context: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.source_code.strip():
            raise ValueError("source_code cannot be empty")

        if not self.language.strip():
            raise ValueError("language cannot be empty")
