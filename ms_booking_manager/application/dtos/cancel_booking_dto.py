from uuid import UUID

from pydantic import BaseModel, Field


class CancelBookingDTO(BaseModel):
    """Input data for cancelling a booking.

    Fields:
        booking_id: Unique identifier for the booking.
        player_id: Player who requests the cancellation.
    """

    booking_id: UUID = Field(..., description="Unique identifier for the booking.")
    player_id: UUID = Field(..., description="Player who requests the cancellation.")

