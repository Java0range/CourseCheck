from functools import wraps
from typing import Any, Callable, Coroutine

from fastapi import HTTPException, Request, status

from src.users.documents import Permissions
from src.users.jwt import security
from src.users.odm import AsyncUsersODM


ROLE_LEVELS = {
    Permissions.STUDENT: 1,
    Permissions.TEACHER: 2,
    Permissions.ADMIN: 3,
}


def normalize_permission(permission: str | Permissions) -> Permissions:
    if isinstance(permission, Permissions):
        return permission

    value = permission.lower()

    try:
        return Permissions(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неизвестная роль пользователя",
        )


async def get_current_user_id(request: Request) -> str:
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недействительный access токен",
        )

    user_id = security.check_access_token(access_token)

    if "Error" in user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недействительный access токен",
        )

    return user_id


async def get_current_user(request: Request):
    user_id = await get_current_user_id(request)
    return await AsyncUsersODM.get_user_by_id(user_id)


async def get_user_permissions(request: Request) -> Permissions:
    user_id = await get_current_user_id(request)
    return await AsyncUsersODM.check_user_permissions(user_id)


async def check_permissions(required_permissions: str | Permissions, request: Request):
    required = normalize_permission(required_permissions)
    user_permissions = await get_user_permissions(request)

    if ROLE_LEVELS[user_permissions] >= ROLE_LEVELS[required]:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Недостаточно прав",
    )


def permission_required(required_permissions: str | Permissions):
    def decorator(endpoint: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(endpoint)
        async def wrapper(request: Request, *args, **kwargs) -> Any:
            await check_permissions(required_permissions, request)
            return await endpoint(request, *args, **kwargs)

        return wrapper

    return decorator


def role_required(*allowed_roles: Permissions):
    def decorator(endpoint: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(endpoint)
        async def wrapper(request: Request, *args, **kwargs) -> Any:
            user_permissions = await get_user_permissions(request)

            if user_permissions in allowed_roles:
                return await endpoint(request, *args, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав",
            )

        return wrapper

    return decorator