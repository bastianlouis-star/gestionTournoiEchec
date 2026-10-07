from app.models.tournament import Tournament
from app.repositories.repository_base import RepositoryBase


class TournamentRepository(RepositoryBase[Tournament]):
    model = Tournament
