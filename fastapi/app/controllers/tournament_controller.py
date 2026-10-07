import math
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.dtos.TournamentDto import (
    PlayerDto, RegistrationStatusDto, TournamentCreateDto, TournamentDto, TournamentListItemDto,
    TournamentPageDto, TournamentUpdateDto,
)
from app.models.registration import Registration
from app.models.tournament import Tournament, TournamentCategory, TournamentStatus
from app.models.user import User
from app.repositories.registration_repository import RegistrationRepository
from app.repositories.tournament_repository import TournamentRepository
from app.repositories.user_repository import UserRepository
from app.services.mailer import Mailer
from app.services.tournament_notifier import (
    build_cancellation_notifications, build_notifications, send_notifications,
)
from app.utils.auth import get_current_user, get_optional_user, require_admin
from app.utils.eligibility import constraint_violations, registration_blockers
from app.utils.tournament_rules import check_elo_range, check_player_range, check_registration_end

router = APIRouter(prefix='/tournaments', tags=['tournaments'])

PAGE_SIZE = 10
TournamentId = Annotated[int, Path(ge=1)]
Repository = Annotated[TournamentRepository, Depends(TournamentRepository)]
UserRepo = Annotated[UserRepository, Depends(UserRepository)]
RegistrationRepo = Annotated[RegistrationRepository, Depends(RegistrationRepository)]


def _get_or_404(repository: TournamentRepository, tournament_id: int) -> Tournament:
    try:
        return repository.get_one(tournament_id)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournoi introuvable.")


def _user_from_token(user_repository: UserRepository, payload: dict) -> User:
    try:
        return user_repository.get_one(payload.get('id'))
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable.")


def _to_list_item(tournament: Tournament, registered_players: int) -> TournamentListItemDto:
    return TournamentListItemDto(
        **TournamentDto.model_validate(tournament).model_dump(), registeredPlayers=registered_players,
    )


def _registration_status(
    tournament: Tournament, user: User, registration_repository: RegistrationRepository,
) -> RegistrationStatusDto:
    """Le joueur peut-il s'inscrire à ce tournoi ? (et pourquoi pas)"""
    registered = registration_repository.count(tournament.id)
    is_full = registered >= tournament.maxPlayers
    is_registered = registration_repository.get(tournament.id, user.id) is not None

    reasons = registration_blockers(tournament) + constraint_violations(user, tournament)
    if is_registered:
        reasons.append("Vous êtes déjà inscrit à ce tournoi.")
    elif is_full:
        reasons.append("Le tournoi est complet.")

    return RegistrationStatusDto(
        canRegister=not reasons, isRegistered=is_registered, isFull=is_full,
        registeredPlayers=registered, reasons=reasons,
    )


@router.get('', response_model=TournamentPageDto)
def list_tournaments(
    repository: Repository,
    user_repository: UserRepo,
    registration_repository: RegistrationRepo,
    name: Annotated[str | None, Query(description="Contient (insensible à la casse)")] = None,
    location: Annotated[str | None, Query(description="Contient (insensible à la casse)")] = None,
    status_filter: Annotated[TournamentStatus | None, Query(alias='status')] = None,
    categories: Annotated[list[TournamentCategory] | None, Query()] = None,
    women_only: Annotated[bool | None, Query(alias='womenOnly')] = None,
    can_register: Annotated[bool | None, Query(alias='canRegister')] = None,
    registered: Annotated[bool | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    payload: Annotated[dict | None, Depends(get_optional_user)] = None,
):
    """Tournois par pages de 10, du plus récemment modifié au plus ancien (accessible à tous).

    Sans filtre `status`, les tournois terminés ne sont pas listés.
    `canRegister` et `registered` concernent le joueur connecté (jeton requis).
    """
    player = None
    if can_register or registered:
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise.")
        player = _user_from_token(user_repository, payload)

    tournaments, total = repository.search(
        name=name, location=location, status=status_filter, categories=categories,
        women_only=women_only,
        eligible_player=player if can_register else None,
        registered_player=player if registered else None,
        page=page, page_size=PAGE_SIZE,
    )
    counts = registration_repository.counts([tournament.id for tournament in tournaments])
    return TournamentPageDto(
        items=[_to_list_item(tournament, counts.get(tournament.id, 0)) for tournament in tournaments],
        total=total,
        page=page,
        pageSize=PAGE_SIZE,
        pages=math.ceil(total / PAGE_SIZE),
    )


@router.get('/{tournament_id}', response_model=TournamentListItemDto)
def get_tournament(tournament_id: TournamentId, repository: Repository, registration_repository: RegistrationRepo):
    tournament = _get_or_404(repository, tournament_id)
    return _to_list_item(tournament, registration_repository.count(tournament.id))


@router.get('/{tournament_id}/players', response_model=list[PlayerDto])
def list_players(tournament_id: TournamentId, repository: Repository, registration_repository: RegistrationRepo):
    """Joueurs inscrits au tournoi, dans l'ordre d'inscription (accessible à tous)."""
    _get_or_404(repository, tournament_id)
    return registration_repository.players(tournament_id)


@router.get('/{tournament_id}/registration', response_model=RegistrationStatusDto)
def get_registration_status(
    tournament_id: TournamentId,
    repository: Repository,
    user_repository: UserRepo,
    registration_repository: RegistrationRepo,
    payload: Annotated[dict, Depends(get_current_user)],
):
    """Le joueur connecté peut-il s'inscrire à ce tournoi ?"""
    tournament = _get_or_404(repository, tournament_id)
    user = _user_from_token(user_repository, payload)
    return _registration_status(tournament, user, registration_repository)


@router.post('/{tournament_id}/registration', response_model=RegistrationStatusDto,
             status_code=status.HTTP_201_CREATED)
def register(
    tournament_id: TournamentId,
    repository: Repository,
    user_repository: UserRepo,
    registration_repository: RegistrationRepo,
    payload: Annotated[dict, Depends(get_current_user)],
):
    """Inscrit le joueur connecté au tournoi s'il respecte toutes les conditions."""
    try:
        # verrou sur le tournoi : deux inscriptions simultanées ne peuvent pas dépasser le maximum
        tournament = repository.get_one_for_update(tournament_id)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournoi introuvable.")
    user = _user_from_token(user_repository, payload)

    current = _registration_status(tournament, user, registration_repository)
    if not current.canRegister:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=' '.join(current.reasons))

    try:
        registration_repository.add(Registration(tournamentId=tournament.id, userId=user.id))
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vous êtes déjà inscrit à ce tournoi.")
    return _registration_status(tournament, user, registration_repository)


@router.delete('/{tournament_id}/registration', response_model=RegistrationStatusDto)
def unregister(
    tournament_id: TournamentId,
    repository: Repository,
    user_repository: UserRepo,
    registration_repository: RegistrationRepo,
    payload: Annotated[dict, Depends(get_current_user)],
):
    """Désinscrit le joueur connecté (possible tant que le tournoi n'a pas commencé)."""
    tournament = _get_or_404(repository, tournament_id)
    user = _user_from_token(user_repository, payload)

    registration = registration_repository.get(tournament.id, user.id)
    if registration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vous n'êtes pas inscrit à ce tournoi.")
    if tournament.status != TournamentStatus.EN_ATTENTE_DE_JOUEURS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Impossible de se désinscrire d'un tournoi qui a commencé.")

    registration_repository.remove(registration)
    return _registration_status(tournament, user, registration_repository)


@router.post('', response_model=TournamentDto, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def create_tournament(
    dto: TournamentCreateDto,
    repository: Repository,
    user_repository: UserRepo,
    background_tasks: BackgroundTasks,
    mailer: Annotated[Mailer, Depends(Mailer)],
):
    try:
        values = dto.model_dump()
        values['categories'] = [category.value for category in dto.categories]
        tournament = repository.add(Tournament(**values))
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un tournoi porte déjà ce nom.")

    # prévenir par mail les joueurs qui respectent les contraintes (envoi après la réponse)
    notifications = build_notifications(tournament, user_repository.get_all())
    background_tasks.add_task(send_notifications, mailer, notifications)
    return tournament


@router.patch('/{tournament_id}', response_model=TournamentDto, dependencies=[Depends(require_admin)])
def update_tournament(
    tournament_id: TournamentId,
    dto: TournamentUpdateDto,
    repository: Repository,
    registration_repository: RegistrationRepo,
):
    tournament = _get_or_404(repository, tournament_id)
    if tournament.status != TournamentStatus.EN_ATTENTE_DE_JOUEURS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Un tournoi commencé ne peut plus être modifié.")

    changes = dto.model_dump(exclude_unset=True)
    # les champs obligatoires ne peuvent pas être mis à null
    for field in ('name', 'minPlayers', 'maxPlayers', 'categories', 'womenOnly', 'registrationEndDate'):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Le champ {field} ne peut pas être vide.")
    if 'categories' in changes:
        changes['categories'] = [category.value for category in changes['categories']]

    min_players = changes.get('minPlayers', tournament.minPlayers)
    max_players = changes.get('maxPlayers', tournament.maxPlayers)
    registration_end = changes.get('registrationEndDate', tournament.registrationEndDate)
    try:
        check_player_range(min_players, max_players)
        check_elo_range(changes.get('minElo', tournament.minElo), changes.get('maxElo', tournament.maxElo))
        # la règle de date ne s'applique que si elle (ou le nb min de joueurs) change
        if 'registrationEndDate' in changes or 'minPlayers' in changes:
            check_registration_end(registration_end, min_players)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))

    registered = registration_repository.count(tournament_id)
    if registered > max_players:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le maximum de joueurs ne peut pas être inférieur au nombre d'inscrits ({registered}).",
        )
    try:
        return repository.update(tournament_id, **changes)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un tournoi porte déjà ce nom.")


@router.post('/{tournament_id}/start', response_model=TournamentDto, dependencies=[Depends(require_admin)])
def start_tournament(tournament_id: TournamentId, repository: Repository, registration_repository: RegistrationRepo):
    tournament = _get_or_404(repository, tournament_id)
    if tournament.status != TournamentStatus.EN_ATTENTE_DE_JOUEURS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce tournoi a déjà commencé.")
    registered = registration_repository.count(tournament_id)
    if registered < tournament.minPlayers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pas assez de joueurs inscrits ({registered}/{tournament.minPlayers} minimum).",
        )
    return repository.update(tournament_id, status=TournamentStatus.EN_COURS, currentRound=1)


@router.delete('/{tournament_id}', status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
def delete_tournament(
    tournament_id: TournamentId,
    repository: Repository,
    registration_repository: RegistrationRepo,
    background_tasks: BackgroundTasks,
    mailer: Annotated[Mailer, Depends(Mailer)],
):
    tournament = _get_or_404(repository, tournament_id)
    if tournament.status != TournamentStatus.EN_ATTENTE_DE_JOUEURS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Seul un tournoi qui n'a pas commencé peut être supprimé.")

    # prévenir les joueurs inscrits (données préparées avant la suppression, envoi après la réponse)
    notifications = build_cancellation_notifications(tournament, registration_repository.players(tournament_id))
    repository.delete(tournament_id)
    background_tasks.add_task(send_notifications, mailer, notifications)
