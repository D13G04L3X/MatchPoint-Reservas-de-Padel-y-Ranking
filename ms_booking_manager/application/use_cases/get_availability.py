from datetime import datetime, time, timedelta

from domain.models.value_objects import TimeSlot
from domain.ports.booking_repository import BookingRepository
from application.dtos.availability_dto import (
    CourtAvailabilityQueryDTO,
    CourtAvailabilityResponseDTO,
    TimeSlotDTO,
)


class GetCourtAvailabilityUseCase:
    """Use case for listing available court time slots."""

    def __init__(self, booking_repository: BookingRepository) -> None:
        self._booking_repository = booking_repository

    async def execute(
        self, dto: CourtAvailabilityQueryDTO
    ) -> CourtAvailabilityResponseDTO:
        """Return available time slots for a court on a given date."""

        if dto.day_end_hour <= dto.day_start_hour:
            raise ValueError("day_end_hour must be greater than day_start_hour.")

        day_start = datetime.combine(dto.date, time(hour=dto.day_start_hour, minute=0))
        day_end = datetime.combine(dto.date, time(hour=dto.day_end_hour, minute=0))
        slot_delta = timedelta(minutes=dto.slot_minutes)

        available_slots: list[TimeSlotDTO] = []
        current = day_start
        while current + slot_delta <= day_end:
            slot = TimeSlot(start_time=current, end_time=current + slot_delta)
            if not await self._booking_repository.exists_overlap(dto.court_id, slot):
                available_slots.append(
                    TimeSlotDTO(start_time=slot.start_time, end_time=slot.end_time)
                )
            current = current + slot_delta

        return CourtAvailabilityResponseDTO(
            court_id=dto.court_id,
            date=dto.date,
            slots=available_slots,
        )

