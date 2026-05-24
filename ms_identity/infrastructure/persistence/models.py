from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from domain.models.enums import MembershipStatus, PlanType
from infrastructure.persistence.database import Base


class PlayerORM(Base):
    """SQLAlchemy model for players."""

    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    membership_status: Mapped[MembershipStatus] = mapped_column(
        SAEnum(MembershipStatus, name="membership_status"), nullable=False
    )
    restriction_active: Mapped[bool] = mapped_column(Boolean, default=False)
    restriction_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MembershipORM(Base):
    """SQLAlchemy model for memberships."""

    __tablename__ = "memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    player_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.id"), index=True
    )
    plan_type: Mapped[PlanType] = mapped_column(
        SAEnum(PlanType, name="plan_type"), nullable=False
    )
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

