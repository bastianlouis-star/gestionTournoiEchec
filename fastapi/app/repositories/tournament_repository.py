from datetime import date

from sqlalchemy import ColumnElement, Date, any_, case, exists, func, literal, or_, select

from app.models.registration import Registration
from app.models.tournament import Tournament, TournamentCategory, TournamentStatus
from app.models.user import User
from app.repositories.repository_base import RepositoryBase
from app.utils.eligibility import JUNIOR_MAX_AGE, SENIOR_MAX_AGE, WOMEN_ONLY_GENRES


class TournamentRepository(RepositoryBase[Tournament]):
    model = Tournament

    def get_one_for_update(self, tournament_id: int) -> Tournament:
        """Charge le tournoi en verrouillant sa ligne (évite de dépasser le maximum de joueurs en cas d'inscriptions simultanées)."""
        return self._session.get_one(self.model, tournament_id, with_for_update=True)

    def _is_registered(self, user: User) -> ColumnElement[bool]:
        return exists().where(Registration.tournamentId == self.model.id, Registration.userId == user.id)

    def _eligibility_conditions(self, user: User) -> list[ColumnElement[bool]]:
        """Version SQL de app.utils.eligibility (registration_blockers + constraint_violations),
        plus « tournoi non plein » et « pas déjà inscrit »."""
        registered_count = (
            select(func.count()).where(Registration.tournamentId == self.model.id).scalar_subquery()
        )
        # catégorie d'âge du joueur à la fin des inscriptions de chaque tournoi
        age_at_registration_end = func.date_part(
            'year', func.age(self.model.registrationEndDate, literal(user.dateOfBirth, Date))
        )
        category = case(
            (age_at_registration_end <= JUNIOR_MAX_AGE, TournamentCategory.JUNIOR.value),
            (age_at_registration_end <= SENIOR_MAX_AGE, TournamentCategory.SENIOR.value),
            else_=TournamentCategory.VETERAN.value,
        )
        conditions = [
            self.model.status == TournamentStatus.EN_ATTENTE_DE_JOUEURS,
            self.model.registrationEndDate >= date.today(),
            or_(self.model.minElo.is_(None), self.model.minElo <= user.elo),
            or_(self.model.maxElo.is_(None), self.model.maxElo >= user.elo),
            category == any_(self.model.categories),
            registered_count < self.model.maxPlayers,
            ~self._is_registered(user),
        ]
        if user.genre not in WOMEN_ONLY_GENRES:
            conditions.append(self.model.womenOnly.is_(False))
        return conditions

    def search(
        self,
        *,
        name: str | None = None,
        location: str | None = None,
        status: TournamentStatus | None = None,
        categories: list[TournamentCategory] | None = None,
        women_only: bool | None = None,
        eligible_player: User | None = None,
        registered_player: User | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Tournament], int]:
        """Recherche paginée, du tournoi le plus récemment modifié au plus ancien.

        Sans filtre de statut, les tournois clôturés (terminés) sont exclus.
        Le filtre de catégories garde les tournois qui acceptent au moins l'une des catégories données.
        `eligible_player` ne garde que les tournois auxquels ce joueur peut s'inscrire (mêmes règles que
        app.utils.eligibility), `registered_player` ceux auxquels il est inscrit.
        """
        conditions = [self.model.status == status if status else self.model.status != TournamentStatus.TERMINE]
        if name:
            conditions.append(self.model.name.icontains(name, autoescape=True))
        if location:
            conditions.append(self.model.location.icontains(location, autoescape=True))
        if categories:
            conditions.append(self.model.categories.overlap([category.value for category in categories]))
        if women_only:
            conditions.append(self.model.womenOnly.is_(True))
        if eligible_player is not None:
            conditions += self._eligibility_conditions(eligible_player)
        if registered_player is not None:
            conditions.append(self._is_registered(registered_player))

        total = self._session.scalar(select(func.count()).select_from(self.model).where(*conditions)) or 0
        query = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.updatedAt.desc(), self.model.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._session.scalars(query).all()), total
