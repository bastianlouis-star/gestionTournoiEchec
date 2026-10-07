from sqlalchemy import func, select

from app.models.match import Match, MatchResult
from app.repositories.repository_base import RepositoryBase


class MatchRepository(RepositoryBase[Match]):
    model = Match

    def get(self, tournament_id: int, match_id: int) -> Match | None:
        return self._session.scalar(
            select(self.model).where(self.model.tournamentId == tournament_id, self.model.id == match_id)
        )

    def last_round(self, tournament_id: int) -> int:
        """Numéro de la dernière ronde du calendrier (0 s'il n'y a aucune rencontre)."""
        return self._session.scalar(
            select(func.max(self.model.round)).where(self.model.tournamentId == tournament_id)
        ) or 0

    def count_unplayed(self, tournament_id: int, round_number: int) -> int:
        return self._session.scalar(
            select(func.count()).select_from(self.model).where(
                self.model.tournamentId == tournament_id,
                self.model.round == round_number,
                self.model.result == MatchResult.NOT_PLAYED,
            )
        ) or 0

    def add_all(self, matches: list[Match]) -> None:
        self._session.add_all(matches)
        self._session.flush()

    def list_for_tournament(
        self, tournament_id: int, round_number: int | None = None, up_to_round: int | None = None,
    ) -> list[Match]:
        """Rencontres du tournoi ; `round_number` = une seule ronde, `up_to_round` = rondes 1 à N."""
        query = select(self.model).where(self.model.tournamentId == tournament_id)
        if round_number is not None:
            query = query.where(self.model.round == round_number)
        if up_to_round is not None:
            query = query.where(self.model.round <= up_to_round)
        return list(self._session.scalars(query.order_by(self.model.round, self.model.id)).all())
