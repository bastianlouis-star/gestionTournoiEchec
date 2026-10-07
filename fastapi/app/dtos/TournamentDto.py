from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.match import MatchResult
from app.models.tournament import TournamentCategory, TournamentStatus
from app.utils.tournament_rules import check_elo_range, check_player_range, check_registration_end


def _unique(categories: list[TournamentCategory] | None) -> list[TournamentCategory] | None:
    if categories is None:
        return None
    return list(dict.fromkeys(categories))


class TournamentCreateDto(BaseModel):
    name: str = Field(min_length=1)
    location: str | None = Field(default=None)
    minPlayers: int = Field(ge=2, le=32)
    maxPlayers: int = Field(ge=2, le=32)
    minElo: int | None = Field(default=None, ge=0, le=3000)
    maxElo: int | None = Field(default=None, ge=0, le=3000)
    categories: list[TournamentCategory] = Field(min_length=1)
    womenOnly: bool = Field(default=False)
    registrationEndDate: date = Field()

    _dedupe_categories = field_validator('categories')(_unique)

    @model_validator(mode='after')
    def check_rules(self):
        check_player_range(self.minPlayers, self.maxPlayers)
        check_elo_range(self.minElo, self.maxElo)
        check_registration_end(self.registrationEndDate, self.minPlayers)
        return self


class TournamentUpdateDto(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    location: str | None = Field(default=None)
    minPlayers: int | None = Field(default=None, ge=2, le=32)
    maxPlayers: int | None = Field(default=None, ge=2, le=32)
    minElo: int | None = Field(default=None, ge=0, le=3000)
    maxElo: int | None = Field(default=None, ge=0, le=3000)
    categories: list[TournamentCategory] | None = Field(default=None, min_length=1)
    womenOnly: bool | None = Field(default=None)
    registrationEndDate: date | None = Field(default=None)

    _dedupe_categories = field_validator('categories')(_unique)


class MatchDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tournamentId: int
    whiteId: int
    blackId: int
    whiteUsername: str | None = None
    blackUsername: str | None = None
    round: int
    result: MatchResult


class ScoreRowDto(BaseModel):
    rank: int
    playerId: int
    username: str
    played: int
    wins: int
    losses: int
    draws: int
    score: float


class ScoreboardDto(BaseModel):
    tournamentId: int
    round: int
    lastRound: int
    rows: list[ScoreRowDto]


class MatchUpdateDto(BaseModel):
    result: MatchResult


class PlayerDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    elo: int


class RegistrationStatusDto(BaseModel):
    canRegister: bool
    isRegistered: bool
    isFull: bool
    registeredPlayers: int
    reasons: list[str]


class TournamentDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str | None
    minPlayers: int
    maxPlayers: int
    minElo: int | None
    maxElo: int | None
    categories: list[TournamentCategory]
    status: TournamentStatus
    currentRound: int
    womenOnly: bool
    registrationEndDate: date
    createdAt: datetime
    updatedAt: datetime


class TournamentListItemDto(TournamentDto):
    registeredPlayers: int


class TournamentPageDto(BaseModel):
    items: list[TournamentListItemDto]
    total: int
    page: int
    pageSize: int
    pages: int
