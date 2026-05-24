from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Court:
    """Court entity.

    Fields:
        id: Unique court identifier.
        name: Human-readable court name.
        description: Court description or notes.
        is_active: True when the court can be booked.
    """

    id: UUID
    name: str
    description: str
    is_active: bool

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise TypeError("Court id must be a UUID.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Court name must be a non-empty string.")
        if not isinstance(self.description, str):
            raise TypeError("Court description must be a string.")
        if not isinstance(self.is_active, bool):
            raise TypeError("Court is_active must be a boolean.")

