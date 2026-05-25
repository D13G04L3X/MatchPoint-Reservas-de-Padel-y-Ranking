from datetime import date as date_type, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.dtos.availability_dto import (
    CourtAvailabilityQueryDTO,
    CourtAvailabilityResponseDTO,
    CourtSummaryDTO,
    CourtsAvailabilityByDateResponseDTO,
)
from application.dtos.booking_response_dto import BookingResponseDTO
from application.dtos.cancel_booking_dto import CancelBookingDTO
from application.dtos.create_booking_dto import CreateBookingDTO
from domain.models.enums import BookingStatus
from domain.services.booking_service import (
    BookingDomainError,
    BookingOverlapError,
    CourtNotFoundError,
    PremiumMembershipRequired,
    PremiumRestricted,
    RankedLevelDifferenceTooHigh,
)
from infrastructure.clients.identity_http_client import IdentityServiceUnavailable
from infrastructure.clients.ranking_http_client import RankingServiceUnavailable
from infrastructure.persistence.postgres_booking_repository import PostgresBookingRepository
from infrastructure.api.dependencies import (
    get_availability_use_case,
    get_booking_repository,
    get_booking_use_case,
    get_cancel_use_case,
    get_court_repository,
    get_courts_availability_use_case,
    get_list_bookings_by_date_use_case,
)
from infrastructure.observability.metrics import (
    bookings_cancelled_late_total,
    bookings_created_total,
    premium_validation_failures_total,
    ranked_validation_failures_total,
)

booking_router = APIRouter()
courts_router = APIRouter()
internal_router = APIRouter(prefix="/internal", include_in_schema=False)


@booking_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BookingResponseDTO,
)
async def create_booking(
    dto: CreateBookingDTO,
    use_case=Depends(get_booking_use_case),
) -> BookingResponseDTO:
    """Create a booking."""

    try:
        created = await use_case.execute(dto)
        bookings_created_total.inc()
        return created
    except BookingOverlapError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CourtNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PremiumMembershipRequired as exc:
        premium_validation_failures_total.inc()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except PremiumRestricted as exc:
        premium_validation_failures_total.inc()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RankedLevelDifferenceTooHigh as exc:
        ranked_validation_failures_total.inc()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (IdentityServiceUnavailable, RankingServiceUnavailable) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@booking_router.get("/by-date", response_model=list[BookingResponseDTO])
async def list_bookings_by_date(
    date_value: date_type = Query(..., alias="date"),
    player_id: UUID | None = Query(
        None, description="If set, only return bookings for this player."
    ),
    include_cancelled: bool = Query(
        False, description="Include cancelled bookings in the response."
    ),
    use_case=Depends(get_list_bookings_by_date_use_case),
) -> list[BookingResponseDTO]:
    """Return bookings scheduled for a given date (club local time)."""

    return await use_case.execute(
        date_value,
        player_id=player_id,
        include_cancelled=include_cancelled,
    )


@booking_router.delete("/{booking_id}", response_model=BookingResponseDTO)
async def cancel_booking(
    booking_id: UUID,
    player_id: UUID = Query(..., description="ID of the player cancelling the booking"),
    use_case=Depends(get_cancel_use_case),
) -> BookingResponseDTO:
    """Cancel an existing booking."""

    try:
        cancelled = await use_case.execute(
            booking_id=booking_id,
            player_id=player_id,
            now=datetime.now(timezone.utc),
        )
        if cancelled.status == BookingStatus.CANCELLED_LATE:
            bookings_cancelled_late_total.inc()
        return cancelled
    except BookingDomainError as exc:
        detail = str(exc)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in detail.lower()
            else status.HTTP_403_FORBIDDEN
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc


@booking_router.get("/{booking_id}", response_model=BookingResponseDTO)
async def get_booking_by_id(
    booking_id: UUID,
    booking_repository: PostgresBookingRepository = Depends(get_booking_repository),
) -> BookingResponseDTO:
    """Return a booking by id."""

    booking = await booking_repository.get_by_id(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return BookingResponseDTO.from_entity(booking)


@courts_router.get("/courts", response_model=list[CourtSummaryDTO])
async def list_courts(
    court_repository=Depends(get_court_repository),
) -> list[CourtSummaryDTO]:
    """Return all active courts in the club catalog."""

    courts = await court_repository.list_active()
    return [
        CourtSummaryDTO(id=court.id, name=court.name, description=court.description)
        for court in courts
    ]


@courts_router.get(
    "/courts/availability",
    response_model=CourtsAvailabilityByDateResponseDTO,
)
async def get_courts_availability(
    date_value: date_type = Query(..., alias="date"),
    slot_minutes: int = 60,
    day_start_hour: int = 6,
    day_end_hour: int = 23,
    use_case=Depends(get_courts_availability_use_case),
) -> CourtsAvailabilityByDateResponseDTO:
    """Return active courts with at least one free slot on a given date."""

    return await use_case.execute(
        date=date_value,
        slot_minutes=slot_minutes,
        day_start_hour=day_start_hour,
        day_end_hour=day_end_hour,
    )


@courts_router.get(
    "/courts/{court_id}/availability",
    response_model=CourtAvailabilityResponseDTO,
)
async def get_court_availability(
    court_id: UUID,
    date_value: date_type = Query(..., alias="date"),
    slot_minutes: int = 60,
    day_start_hour: int = 6,
    day_end_hour: int = 23,
    use_case=Depends(get_availability_use_case),
) -> CourtAvailabilityResponseDTO:
    """Return available slots for a court on a given date."""

    dto = CourtAvailabilityQueryDTO(
        court_id=court_id,
        date=date_value,
        slot_minutes=slot_minutes,
        day_start_hour=day_start_hour,
        day_end_hour=day_end_hour,
    )
    return await use_case.execute(dto)


@internal_router.get(
    "/bookings/player/{player_id}",
    response_model=list[BookingResponseDTO],
)
async def list_bookings_by_player(
    player_id: UUID,
    booking_repository: PostgresBookingRepository = Depends(get_booking_repository),
) -> list[BookingResponseDTO]:
    """Return bookings for a player (internal endpoint)."""

    bookings = await booking_repository.get_by_player(player_id)
    return [BookingResponseDTO.from_entity(booking) for booking in bookings]

