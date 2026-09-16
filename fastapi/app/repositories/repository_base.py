from abc import ABC
from typing import Annotated, Any, Generic, TypeVar

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import get_session

T = TypeVar('T')

class RepositoryBase(ABC, Generic[T]):
    model: type[T]

    def __init__(self, session: Annotated[Session, Depends(get_session)]):
        super().__init__()
        self._session = session

    def get_all(self) -> list[T]:
        return list(self._session.scalars(select(self.model)).all())

    def get_one(self, ident: Any) -> T:
        return self._session.get_one(self.model, ident)

    def add(self, entity: T) -> T:
        self._session.add(entity)
        self._session.flush()
        return entity

    def update(self, ident: Any , **kwargs: Any) -> T:
        entity = self.get_one(ident)
        for field, value in kwargs.items():
            setattr(entity, field, value)
        self._session.flush()
        return entity

    def delete(self, ident: Any) -> T:
        entity = self.get_one(ident)
        self._session.delete(entity)
        self._session.flush()
        return entity

    def flush(self):
       self._session.flush() 