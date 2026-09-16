import enum
from datetime import date

from app.models.base import Base
from sqlalchemy import CheckConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column


class Genre(str, enum.Enum):
    FILLE = "fille"
    GARCON = "garçon"
    AUTRE = "autre"


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint('elo >= 0 AND elo <= 3000', name='elo_range'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    dateOfBirth: Mapped[date] = mapped_column(nullable=False)
    genre: Mapped[Genre] = mapped_column(SqlEnum(Genre), nullable=False)
    elo: Mapped[int] = mapped_column(nullable=False, default=1200)
    isAdmin: Mapped[bool] = mapped_column(nullable=False, default=False)