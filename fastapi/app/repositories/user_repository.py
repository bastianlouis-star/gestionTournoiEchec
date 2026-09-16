from sqlalchemy import select

from app.models.user import User
from app.repositories.repository_base import RepositoryBase


class UserRepository(RepositoryBase[User]):
    model = User

    def get_by_username(self, username: str) -> User | None:
        return self._session.scalar(select(self.model).where(self.model.username == username))
