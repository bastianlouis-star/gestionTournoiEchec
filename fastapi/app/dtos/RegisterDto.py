from datetime import date

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Genre


class RegisterDto(BaseModel):
    username: str = Field()
    password: str | None = Field(default=None)
    email: EmailStr = Field()
    dateOfBirth: date = Field()
    genre: Genre = Field()
    elo: int | None = Field(default=None, ge=0, le=3000)