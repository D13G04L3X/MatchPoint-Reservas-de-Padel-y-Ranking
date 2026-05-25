from datetime import date as Date

from application.dtos.availability_dto import (
    CourtAvailabilityQueryDTO,
    CourtAvailabilitySummaryDTO,
    CourtsAvailabilityByDateResponseDTO,
)
from application.use_cases.get_availability import GetCourtAvailabilityUseCase
from domain.ports.court_repository import CourtRepository


class GetCourtsAvailabilityUseCase:
    """Use case for listing court availability summaries on a given date."""

    def __init__(
        self,
        court_repository: CourtRepository,
        availability_use_case: GetCourtAvailabilityUseCase,
    ) -> None:
        self._court_repository = court_repository
        self._availability_use_case = availability_use_case

    async def execute(
        self,
        date: Date,
        slot_minutes: int = 60,
        day_start_hour: int = 6,
        day_end_hour: int = 23,
    ) -> CourtsAvailabilityByDateResponseDTO:
        """Return availability summaries for all active courts."""

        courts = await self._court_repository.list_active()
        summaries: list[CourtAvailabilitySummaryDTO] = []

        for court in courts:
            availability = await self._availability_use_case.execute(
                CourtAvailabilityQueryDTO(
                    court_id=court.id,
                    date=date,
                    slot_minutes=slot_minutes,
                    day_start_hour=day_start_hour,
                    day_end_hour=day_end_hour,
                )
            )
            slot_count = len(availability.slots)
            summaries.append(
                CourtAvailabilitySummaryDTO(
                    id=court.id,
                    name=court.name,
                    description=court.description,
                    available_slots=slot_count,
                    has_availability=slot_count > 0,
                )
            )

        return CourtsAvailabilityByDateResponseDTO(
            date=date,
            courts=[summary for summary in summaries if summary.has_availability],
        )
