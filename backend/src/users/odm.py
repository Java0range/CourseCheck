from dataclasses import dataclass
from typing import Optional

import bcrypt
from beanie import PydanticObjectId
from fastapi import HTTPException, status
from passlib.context import CryptContext

from src.users.documents import Permissions, UsersDocument
from src.users.schemas import (
    CreatedUserResponseSchema,
    CurrentUserResponseSchema,
    UserResponseSchema,
)


@dataclass
class SolveBugBcryptWarning:
    __version__: str = getattr(bcrypt, "__version__")


setattr(bcrypt, "__about__", SolveBugBcryptWarning())

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def parse_object_id(value: str, error_text: str = "Неверный id") -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_text,
        )


class AsyncUsersODM:
    @staticmethod
    async def insert_user(
        username: str,
        password: str,
        name: str,
        last_name: str,
        permissions: Permissions,
        group_id: Optional[PydanticObjectId] = None,
    ) -> UsersDocument:
        existing_user = await UsersDocument.find_one(
            UsersDocument.username == username
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Имя пользователя уже занято",
            )

        hashed_password = await get_password_hash(password)

        user = UsersDocument(
            username=username,
            password=hashed_password,
            name=name,
            last_name=last_name,
            permissions=permissions,
            group_id=group_id,
        )

        await user.insert()
        return user

    @staticmethod
    async def verify(username: str, password: str) -> PydanticObjectId:
        user = await UsersDocument.find_one(UsersDocument.username == username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Неверный логин или пароль",
            )

        if await verify_password(
            plain_password=password,
            hashed_password=user.password,
        ):
            return user.id

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный логин или пароль",
        )

    @staticmethod
    async def get_user_by_id(user_id: str | PydanticObjectId) -> UsersDocument:
        if not isinstance(user_id, PydanticObjectId):
            user_id = parse_object_id(str(user_id), "Неверный id пользователя")

        user = await UsersDocument.find_one(UsersDocument.id == user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        return user

    @staticmethod
    async def get_current_user_response(
        user_id: str | PydanticObjectId,
    ) -> CurrentUserResponseSchema:
        user = await AsyncUsersODM.get_user_by_id(user_id)

        return CurrentUserResponseSchema(
            id=user.id,
            username=user.username,
            name=user.name,
            last_name=user.last_name,
            permissions=user.permissions,
            group_id=user.group_id,
        )

    @staticmethod
    async def check_user_permissions(user_id: str) -> Permissions:
        user = await AsyncUsersODM.get_user_by_id(user_id)
        return user.permissions

    @staticmethod
    async def delete_user(user_id: str) -> None:
        user = await AsyncUsersODM.get_user_by_id(user_id)
        await user.delete()

    @staticmethod
    async def update_user(
        user_id: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        name: Optional[str] = None,
        last_name: Optional[str] = None,
        permissions: Optional[Permissions] = None,
        group_id: Optional[PydanticObjectId] = None,
    ) -> UsersDocument:
        user = await AsyncUsersODM.get_user_by_id(user_id)

        if username and username != user.username:
            existing_user = await UsersDocument.find_one(
                UsersDocument.username == username
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Имя пользователя уже занято",
                )

            user.username = username

        if password:
            user.password = await get_password_hash(password)

        if name is not None:
            user.name = name

        if last_name is not None:
            user.last_name = last_name

        if permissions is not None:
            user.permissions = permissions

        if group_id is not None:
            user.group_id = group_id

        await user.save()
        return user

    @staticmethod
    async def get_all_users(
        permissions: Optional[Permissions] = None,
        group_id: Optional[PydanticObjectId] = None,
    ) -> list[UserResponseSchema]:
        query = {}

        if permissions is not None:
            query["permissions"] = permissions

        if group_id is not None:
            query["group_id"] = group_id

        users = await UsersDocument.find(query).to_list()

        return [
            UserResponseSchema(
                id=user.id,
                username=user.username,
                name=user.name,
                last_name=user.last_name,
                permissions=user.permissions,
                group_id=user.group_id,
            )
            for user in users
        ]

    @staticmethod
    async def to_user_response(user: UsersDocument) -> UserResponseSchema:
        return UserResponseSchema(
            id=user.id,
            username=user.username,
            name=user.name,
            last_name=user.last_name,
            permissions=user.permissions,
            group_id=user.group_id,
        )

    @staticmethod
    async def to_created_response(
        user: UsersDocument,
        temporary_password: Optional[str] = None,
    ) -> CreatedUserResponseSchema:
        return CreatedUserResponseSchema(
            id=user.id,
            username=user.username,
            name=user.name,
            last_name=user.last_name,
            permissions=user.permissions,
            group_id=user.group_id,
            temporary_password=temporary_password,
        )