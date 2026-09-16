from pydantic import BaseModel, EmailStr, Field


class LoginDto(BaseModel):
    username: str = Field()
    password: str = Field()