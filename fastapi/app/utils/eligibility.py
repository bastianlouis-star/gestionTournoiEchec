from datetime import date

from app.models.tournament import Tournament, TournamentCategory, TournamentStatus
from app.models.user import Genre, User

# Tranches d'âge des catégories (âge en années révolues) : Junior < 18, Senior 18-59, Vétéran >= 60
JUNIOR_MAX_AGE = 17
SENIOR_MAX_AGE = 59

# Genres admis dans un tournoi « women only »
WOMEN_ONLY_GENRES = (Genre.FILLE, Genre.AUTRE)


def age_on(date_of_birth: date, reference_date: date) -> int:
    return (
        reference_date.year - date_of_birth.year
        - ((reference_date.month, reference_date.day) < (date_of_birth.month, date_of_birth.day))
    )


def player_category(date_of_birth: date, reference_date: date) -> TournamentCategory:
    """Catégorie d'âge du joueur à la date donnée (pour un tournoi : la fin des inscriptions)."""
    age = age_on(date_of_birth, reference_date)
    if age <= JUNIOR_MAX_AGE:
        return TournamentCategory.JUNIOR
    if age <= SENIOR_MAX_AGE:
        return TournamentCategory.SENIOR
    return TournamentCategory.VETERAN


def constraint_violations(user: User, tournament: Tournament) -> list[str]:
    """Raisons pour lesquelles le profil du joueur ne correspond pas au tournoi (elo, mixité, âge).

    L'âge est celui que le joueur aura à la date de fin des inscriptions du tournoi.
    """
    reasons = []
    if tournament.minElo is not None and user.elo < tournament.minElo:
        reasons.append(f"Votre elo ({user.elo}) est inférieur au minimum requis ({tournament.minElo}).")
    if tournament.maxElo is not None and user.elo > tournament.maxElo:
        reasons.append(f"Votre elo ({user.elo}) est supérieur au maximum autorisé ({tournament.maxElo}).")
    if tournament.womenOnly and user.genre not in WOMEN_ONLY_GENRES:
        reasons.append("Ce tournoi est réservé aux joueuses (genre « fille » ou « autre »).")
    category = player_category(user.dateOfBirth, tournament.registrationEndDate)
    if category.value not in tournament.categories:
        reasons.append(
            f"Votre catégorie d'âge à la fin des inscriptions ({category.value}) n'est pas acceptée dans ce tournoi."
        )
    return reasons


def respects_constraints(user: User, tournament: Tournament) -> bool:
    """Un joueur peut participer s'il respecte la plage d'elo, la mixité et les catégories du tournoi."""
    return not constraint_violations(user, tournament)


def registration_blockers(tournament: Tournament, today: date | None = None) -> list[str]:
    """Raisons liées au tournoi lui-même (statut, date limite)."""
    reasons = []
    if tournament.status != TournamentStatus.EN_ATTENTE_DE_JOUEURS:
        reasons.append("Les inscriptions sont closes pour ce tournoi.")
    elif tournament.registrationEndDate < (today or date.today()):
        reasons.append("La date limite d'inscription est dépassée.")
    return reasons
