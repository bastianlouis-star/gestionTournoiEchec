from datetime import datetime

from app.models.base import Base
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column


class Registration(Base):
    """Inscription d'un joueur à un tournoi (supprimée avec le tournoi ou le joueur)."""
    __tablename__ = 'registrations'
    __table_args__ = (
        UniqueConstraint('tournamentId', 'userId', name='uq_registration_player'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tournamentId: Mapped[int] = mapped_column(
        ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False, index=True
    )
    userId: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
