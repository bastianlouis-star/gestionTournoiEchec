import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError

from app.dtos.LoginDto import LoginDto
from app.dtos.RegisterDto import RegisterDto

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.jwt import generate_jwt, verify_jwt
from app.utils.password import *
from app.services.mailer import Mailer


router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', status_code=201)
async def register(
    dto: RegisterDto,
    repository: Annotated[UserRepository, Depends(UserRepository)],
    mailer: Mailer = Depends(Mailer),
):
    password_generated = not dto.password
    if password_generated:
        dto.password = secrets.token_urlsafe(12)

    hashPassword = hash_password(dto.password)
    user_kwargs = dict(
        username=dto.username,
        password=hashPassword,
        email=dto.email,
        dateOfBirth=dto.dateOfBirth,
        genre=dto.genre,
    )
    if dto.elo:
        user_kwargs['elo'] = dto.elo

    user = User(**user_kwargs)
    try:
        repository.add(user)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nom d'utilisateur ou email déjà utilisé.")

    mail_body = dict(dto)
    if not password_generated:
        mail_body.pop('password', None)

    await mailer.send_message(
        "Votre compte a bien été créé",
        dest=[dto.email],
        template_body=mail_body,
        template_name='new_user.html'
    )

@router.post('/login', status_code=200)
def login(
    dto: LoginDto,
    repository: Annotated[UserRepository, Depends(UserRepository)],
):
    user = repository.get_by_username(dto.username)

    if user is None or not verify_password(dto.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides.")

    role = 'admin' if user.isAdmin else 'player'
    return {'access_token': generate_jwt(subject=user.username, role=role, id=user.id)}

@router.get('/{jwt}')
def validate(
    jwt: Annotated[str, Path()]
):
    try:
        return verify_jwt(jwt)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error))