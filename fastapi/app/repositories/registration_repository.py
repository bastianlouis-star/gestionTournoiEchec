from sqlalchemy import func, select

from app.models.registration import Registration
from app.models.user import User
from app.repositories.repository_base import RepositoryBase


class RegistrationRepository(RepositoryBase[Registration]):
    model = Registration

    def get(self, tournament_id: int, user_id: int) -> Registration | None:
        return self._session.scalar(
            select(self.model).where(self.model.tournamentId == tournament_id, self.model.userId == user_id)
        )

    def players(self, tournament_id: int) -> list[User]:
        """Joueurs inscrits, dans l'ordre d'inscription."""
        query = (
            select(User)
            .join(self.model, self.model.userId == User.id)
            .where(self.model.tournamentId == tournament_id)
            .order_by(self.model.createdAt, self.model.id)
        )
        return list(self._session.scalars(query).all())

    def count(self, tournament_id: int) -> int:
        return self._session.scalar(
            select(func.count()).select_from(self.model).where(self.model.tournamentId == tournament_id)
        ) or 0

    def counts(self, tournament_ids: list[int]) -> dict[int, int]:
        """Nombre d'inscrits pour plusieurs tournois en une requête."""
        if not tournament_ids:
            return {}
        rows = self._session.execute(
            select(self.model.tournamentId, func.count())
            .where(self.model.tournamentId.in_(tournament_ids))
            .group_by(self.model.tournamentId)
        ).all()
        return {tournament_id: total for tournament_id, total in rows}

    def remove(self, registration: Registration) -> None:
        self._session.delete(registration)
        self._session.flush()
