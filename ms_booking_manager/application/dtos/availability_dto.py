from datetime import date as Date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TimeSlotDTO(BaseModel):
    """Time slot representation for availability responses.

    Fields:
        start_time: Start of the available time window.
        end_time: End of the available time window.
    """

    start_time: datetime = Field(..., description="Start of the available time window.")
    end_time: datetime = Field(..., description="End of the available time window.")


class CourtAvailabilityQueryDTO(BaseModel):
    """Query data for court availability.

    Fields:
        court_id: Court to query.
        date: Date for the availability window.
        slot_minutes: Duration of each slot in minutes.
        day_start_hour: Hour when availability starts.
        day_end_hour: Hour when availability ends.
    """

    court_id: UUID = Field(..., description="Court to query.")
    date: Date = Field(..., description="Date for the availability window.")
    slot_minutes: int = Field(
        ..., gt=0, le=1440, description="Duration of each slot in minutes."
    )
    day_start_hour: int = Field(
        6, ge=0, le=23, description="Hour when availability starts."
    )
    day_end_hour: int = Field(23, ge=1, le=24, description="Hour when availability ends.")


class CourtAvailabilityResponseDTO(BaseModel):
    """Availability response for a court.

    Fields:
        court_id: Court for which availability is returned.
        date: Date of the availability window.
        slots: Available time slots.
    """
    court_id: UUID = Field(..., description="Court for which availability is returned.")
    date: Date = Field(..., description="Date of the availability window.")
    slots: list[TimeSlotDTO] = Field(
        default_factory=list, description="Available time slots."
    )


class CourtAvailabilitySummaryDTO(BaseModel):
    """Availability summary for one court on a date."""

    id: UUID = Field(..., description="Court identifier.")
    name: str = Field(..., description="Court name.")
    description: str = Field(..., description="Court description.")
    available_slots: int = Field(..., ge=0, description="Number of free slots.")
    has_availability: bool = Field(..., description="True when at least one slot is free.")


class CourtsAvailabilityByDateResponseDTO(BaseModel):
    """Availability summaries for all active courts on a date."""

    date: Date = Field(..., description="Date queried.")
    courts: list[CourtAvailabilitySummaryDTO] = Field(
        default_factory=list, description="Availability per court."
    )


class CourtSummaryDTO(BaseModel):
    """Active court in the club catalog."""

    id: UUID = Field(..., description="Court identifier.")
    name: str = Field(..., description="Court name.")
    description: str = Field(..., description="Court description.")

