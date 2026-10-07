from datetime import date

from app.models.tournament import Tournament, TournamentCategory
from app.models.user import Genre, User

# Tranches d'âge des catégories (âge en années révolues)
JUNIOR_MAX_AGE = 17
SENIOR_MAX_AGE = 59


def age_on(date_of_birth: date, today: date) -> int:
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))


def player_category(date_of_birth: date, today: date | None = None) -> TournamentCategory:
    age = age_on(date_of_birth, today or date.today())
    if age <= JUNIOR_MAX_AGE:
        return TournamentCategory.JUNIOR
    if age <= SENIOR_MAX_AGE:
        return TournamentCategory.SENIOR
    return TournamentCategory.VETERAN


def respects_constraints(user: User, tournament: Tournament, today: date | None = None) -> bool:
    """Un joueur peut participer s'il respecte la plage d'elo, la mixité et les catégories du tournoi."""
    if tournament.minElo is not None and user.elo < tournament.minElo:
        return False
    if tournament.maxElo is not None and user.elo > tournament.maxElo:
        return False
    if tournament.womenOnly and user.genre != Genre.FILLE:
        return False
    return player_category(user.dateOfBirth, today).value in tournament.categories
