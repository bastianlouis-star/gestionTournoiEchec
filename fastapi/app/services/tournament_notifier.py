import logging

from app.models.tournament import Tournament, TournamentCategory
from app.models.user import User
from app.services.mailer import Mailer
from app.utils.eligibility import respects_constraints

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    TournamentCategory.JUNIOR.value: 'Junior',
    TournamentCategory.SENIOR.value: 'Senior',
    TournamentCategory.VETERAN.value: 'Vétéran',
}


def _format_elo(tournament: Tournament) -> str:
    low, high = tournament.minElo, tournament.maxElo
    if low is None and high is None:
        return 'tous niveaux'
    if low is None:
        return f"jusqu'à {high}"
    if high is None:
        return f"à partir de {low}"
    return f'{low} – {high}'


def eligible_players(tournament: Tournament, users: list[User]) -> list[User]:
    return [user for user in users if respects_constraints(user, tournament)]


def build_notifications(tournament: Tournament, users: list[User]) -> list[dict]:
    """Prépare les mails (données simples, indépendantes de la session SQLAlchemy)."""
    body = {
        'name': tournament.name,
        'location': tournament.location,
        'min_players': tournament.minPlayers,
        'max_players': tournament.maxPlayers,
        'elo': _format_elo(tournament),
        'categories': ', '.join(CATEGORY_LABELS[category] for category in tournament.categories),
        'women_only': tournament.womenOnly,
        'registration_end_date': tournament.registrationEndDate.strftime('%d/%m/%Y'),
    }
    return [
        {
            'email': user.email,
            'subject': f'Nouveau tournoi : {tournament.name}',
            'template': 'tournament_created.html',
            'body': {**body, 'username': user.username},
        }
        for user in eligible_players(tournament, users)
    ]


def build_cancellation_notifications(tournament: Tournament, registered_players: list[User]) -> list[dict]:
    """Prépare les mails prévenant les joueurs inscrits que le tournoi est supprimé."""
    return [
        {
            'email': user.email,
            'subject': f'Tournoi supprimé : {tournament.name}',
            'template': 'tournament_deleted.html',
            'body': {'name': tournament.name, 'username': user.username},
        }
        for user in registered_players
    ]


async def send_notifications(mailer: Mailer, notifications: list[dict]) -> None:
    """Un mail par joueur (pour ne pas exposer les adresses des autres) ; un échec n'arrête pas les suivants."""
    for notification in notifications:
        try:
            await mailer.send_message(
                notification['subject'],
                dest=[notification['email']],
                template_body=notification['body'],
                template_name=notification['template'],
            )
        except Exception:
            logger.exception("Échec de l'envoi du mail à %s", notification['email'])
