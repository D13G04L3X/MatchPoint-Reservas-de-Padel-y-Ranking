from datetime import date as Date, datetime, time, timedelta
from uuid import UUID

from domain.models.value_objects import CLUB_TIMEZONE, TimeSlot
from domain.ports.booking_repository import BookingRepository
from application.dtos.availability_dto import (
    CourtAvailabilityQueryDTO,
    CourtAvailabilityResponseDTO,
    TimeSlotDTO,
)


async def compute_available_slots(
    booking_repository: BookingRepository,
    court_id: UUID,
    date: Date,
    slot_minutes: int,
    day_start_hour: int,
    day_end_hour: int,
) -> list[TimeSlotDTO]:
    """Return free slots for one court on a given date (club local time)."""

    if day_end_hour <= day_start_hour:
        raise ValueError("day_end_hour must be greater than day_start_hour.")

    day_start = datetime.combine(
        date, time(hour=day_start_hour, minute=0), tzinfo=CLUB_TIMEZONE
    )
    day_end = datetime.combine(
        date, time(hour=day_end_hour, minute=0), tzinfo=CLUB_TIMEZONE
    )
    slot_delta = timedelta(minutes=slot_minutes)

    available_slots: list[TimeSlotDTO] = []
    current = day_start
    while current + slot_delta <= day_end:
        slot = TimeSlot(start_time=current, end_time=current + slot_delta)
        if not await booking_repository.exists_overlap(court_id, slot):
            available_slots.append(
                TimeSlotDTO(start_time=slot.start_time, end_time=slot.end_time)
            )
        current = current + slot_delta

    return available_slots


class GetCourtAvailabilityUseCase:
    """Use case for listing available court time slots."""

    def __init__(self, booking_repository: BookingRepository) -> None:
        self._booking_repository = booking_repository

    async def execute(
        self, dto: CourtAvailabilityQueryDTO
    ) -> CourtAvailabilityResponseDTO:
        """Return available time slots for a court on a given date."""

        slots = await compute_available_slots(
            self._booking_repository,
            dto.court_id,
            dto.date,
            dto.slot_minutes,
            dto.day_start_hour,
            dto.day_end_hour,
        )
        return CourtAvailabilityResponseDTO(
            court_id=dto.court_id,
            date=dto.date,
            slots=slots,
        )
