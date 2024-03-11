from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from schemas.enums import EnumGenderType


class UserCredentials(BaseModel):
    login: str
    password: str
    remember_me: Optional[bool] = False


class Refresh(BaseModel):
    refresh: str


class SignUp(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    surname: str
    patronymic: Optional[str]
    gender: Optional[EnumGenderType]
    phone: Optional[str]
    date_of_birth: Optional[datetime]
    student: bool
