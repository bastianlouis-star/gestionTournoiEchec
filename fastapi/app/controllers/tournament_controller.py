from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.dtos.TournamentDto import TournamentCreateDto, TournamentDto, TournamentUpdateDto
from app.models.tournament import Tournament, TournamentStatus
from app.repositories.tournament_repository import TournamentRepository
from app.repositories.user_repository import UserRepository
from app.services.mailer import Mailer
from app.services.tournament_notifier import build_notifications, send_notifications
from app.utils.auth import require_admin
from app.utils.tournament_rules import check_elo_range, check_player_range, check_registration_end

router = APIRouter(prefix='/tournaments', tags=['tournaments'])

TournamentId = Annotated[int, Path(ge=1)]
Repository = Annotated[TournamentRepository, Depends(TournamentRepository)]


def _get_or_404(repository: TournamentRepository, tournament_id: int) -> Tournament:
    try:
        return repository.get_one(tournament_id)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournoi introuvable.")


@router.get('', response_model=list[TournamentDto])
def list_tournaments(repository: Repository):
    return repository.get_all()


@router.get('/{tournament_id}', response_model=TournamentDto)
def get_tournament(tournament_id: TournamentId, repository: Repository):
    return _get_or_404(repository, tournament_id)


@router.post('', response_model=TournamentDto, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def create_tournament(
    dto: TournamentCreateDto,
    repository: Repository,
    user_repository: Annotated[UserRepository, Depends(UserRepository)],
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
    background_tasks.add_task(send_notifications, mailer, tournament.name, notifications)
    return tournament


@router.patch('/{tournament_id}', response_model=TournamentDto, dependencies=[Depends(require_admin)])
def update_tournament(tournament_id: TournamentId, dto: TournamentUpdateDto, repository: Repository):
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
    registration_end = changes.get('registrationEndDate', tournament.registrationEndDate)
    try:
        check_player_range(min_players, changes.get('maxPlayers', tournament.maxPlayers))
        check_elo_range(changes.get('minElo', tournament.minElo), changes.get('maxElo', tournament.maxElo))
        # la règle de date ne s'applique que si elle (ou le nb min de joueurs) change
        if 'registrationEndDate' in changes or 'minPlayers' in changes:
            check_registration_end(registration_end, min_players)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    try:
        return repository.update(tournament_id, **changes)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un tournoi porte déjà ce nom.")


@router.delete('/{tournament_id}', status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
def delete_tournament(tournament_id: TournamentId, repository: Repository):
    tournament = _get_or_404(repository, tournament_id)
    if tournament.status == TournamentStatus.EN_COURS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Impossible de supprimer un tournoi en cours.")
    repository.delete(tournament_id)
