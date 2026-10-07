import enum
from datetime import date, datetime

from app.models.base import Base
from sqlalchemy import CheckConstraint, DateTime, String, false, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column


class TournamentStatus(str, enum.Enum):
    EN_ATTENTE_DE_JOUEURS = "en_attente_de_joueurs"
    EN_COURS = "en_cours"
    TERMINE = "termine"


class TournamentCategory(str, enum.Enum):
    JUNIOR = "junior"
    SENIOR = "senior"
    VETERAN = "veteran"


class Tournament(Base):
    __tablename__ = 'tournaments'
    __table_args__ = (
        CheckConstraint('"minPlayers" BETWEEN 2 AND 32', name='min_players_range'),
        CheckConstraint('"maxPlayers" BETWEEN 2 AND 32', name='max_players_range'),
        CheckConstraint('"minPlayers" <= "maxPlayers"', name='players_order'),
        CheckConstraint('"minElo" BETWEEN 0 AND 3000', name='min_elo_range'),
        CheckConstraint('"maxElo" BETWEEN 0 AND 3000', name='max_elo_range'),
        CheckConstraint('"minElo" <= "maxElo"', name='elo_order'),
        CheckConstraint(
            'cardinality(categories) >= 1 '
            "AND categories <@ CAST(ARRAY['junior','senior','veteran'] AS varchar[])",
            name='categories_valid',
        ),
        CheckConstraint('"currentRound" >= 0', name='current_round_min'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    location: Mapped[str | None] = mapped_column(nullable=True)
    minPlayers: Mapped[int] = mapped_column(nullable=False)
    maxPlayers: Mapped[int] = mapped_column(nullable=False)
    minElo: Mapped[int | None] = mapped_column(nullable=True)
    maxElo: Mapped[int | None] = mapped_column(nullable=True)
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    status: Mapped[TournamentStatus] = mapped_column(
        SqlEnum(TournamentStatus), nullable=False, default=TournamentStatus.EN_ATTENTE_DE_JOUEURS
    )
    currentRound: Mapped[int] = mapped_column(nullable=False, default=0, server_default='0')
    womenOnly: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=false())
    registrationEndDate: Mapped[date] = mapped_column(nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
