from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel

from src.users.documents import Permissions


class LoginUserSchema(BaseModel):
    username: str
    password: str


class CreateUserSchema(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    name: str
    last_name: str

    permissions: Permissions = Permissions.STUDENT

    group_id: Optional[PydanticObjectId] = None


class UpdateUserSchema(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    name: Optional[str] = None
    last_name: Optional[str] = None

    permissions: Optional[Permissions] = None

    group_id: Optional[PydanticObjectId] = None


class UserResponseSchema(BaseModel):
    id: PydanticObjectId

    username: str

    name: str
    last_name: str

    permissions: Permissions

    group_id: Optional[PydanticObjectId] = None


class CreatedUserResponseSchema(UserResponseSchema):
    temporary_password: Optional[str] = None


class CurrentUserResponseSchema(BaseModel):
    id: PydanticObjectId
    username: str
    name: str
    last_name: str
    permissions: Permissions
    group_id: Optional[PydanticObjectId] = None