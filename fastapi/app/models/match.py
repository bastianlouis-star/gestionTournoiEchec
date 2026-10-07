import enum

from app.models.base import Base
from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column


class MatchResult(str, enum.Enum):
    NOT_PLAYED = "pas_encore_joue"
    WHITE = "blanc"
    BLACK = "noir"
    DRAW = "egalite"


class Match(Base):
    """Rencontre entre deux joueurs d'un tournoi, pour une ronde donnée."""
    __tablename__ = 'matches'
    __table_args__ = (
        CheckConstraint('"whiteId" <> "blackId"', name='match_distinct_players'),
        CheckConstraint('round >= 1', name='match_round_min'),
        # dans un aller-retour, chaque couple (blanc, noir) n'existe qu'une fois par tournoi
        UniqueConstraint('tournamentId', 'whiteId', 'blackId', name='uq_match_pairing'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tournamentId: Mapped[int] = mapped_column(
        ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False, index=True
    )
    whiteId: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    blackId: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    round: Mapped[int] = mapped_column(nullable=False)
    result: Mapped[MatchResult] = mapped_column(
        SqlEnum(MatchResult), nullable=False, default=MatchResult.NOT_PLAYED
    )
