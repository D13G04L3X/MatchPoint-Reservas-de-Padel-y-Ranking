from datetime import date as date_type, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.dtos.availability_dto import (
    CourtAvailabilityQueryDTO,
    CourtAvailabilityResponseDTO,
)
from application.dtos.booking_response_dto import BookingResponseDTO
from application.dtos.cancel_booking_dto import CancelBookingDTO
from application.dtos.create_booking_dto import CreateBookingDTO
from domain.services.booking_service import (
    BookingDomainError,
    BookingOverlapError,
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
        return await use_case.execute(dto)
    except BookingOverlapError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PremiumMembershipRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except PremiumRestricted as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RankedLevelDifferenceTooHigh as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (IdentityServiceUnavailable, RankingServiceUnavailable) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@booking_router.delete("/{booking_id}", response_model=BookingResponseDTO)
async def cancel_booking(
    booking_id: UUID,
    player_id: UUID = Query(..., description="ID of the player cancelling the booking"),
    use_case=Depends(get_cancel_use_case),
) -> BookingResponseDTO:
    """Cancel an existing booking."""

    try:
        return await use_case.execute(
            booking_id=booking_id,
            player_id=player_id,
            now=datetime.now(timezone.utc),
        )
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

