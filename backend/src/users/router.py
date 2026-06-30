from secrets import token_urlsafe
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Request, Response, status

from src.users.documents import Permissions
from src.users.jwt import security
from src.users.odm import AsyncUsersODM
from src.users.schemas import CreateUserSchema, LoginUserSchema, UpdateUserSchema
from src.users.utils import get_current_user_id, permission_required


router = APIRouter(prefix="/users", tags=["Users & Auth"])


def generate_password() -> str:
    return token_urlsafe(8)


@router.post("/login")
async def login_user(json: LoginUserSchema, response: Response):
    user_id = await AsyncUsersODM.verify(
        username=json.username,
        password=json.password,
    )

    response.set_cookie(
        key="access_token",
        value=security.create_access_token(user_id=str(user_id)),
        httponly=True,
        max_age=1800,
    )

    response.set_cookie(
        key="refresh_token",
        value=security.create_refresh_token(user_id=str(user_id)),
        httponly=True,
        max_age=604800,
    )

    return {"detail": "Успешный вход"}


@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"detail": "Успешный выход"}


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалидный refresh токен",
        )

    response.set_cookie(
        key="access_token",
        value=security.check_refresh_token(refresh_token=token),
        httponly=True,
        max_age=1800,
    )

    return {"detail": "Токен обновлён"}


@router.get("/me")
async def get_user_info(request: Request):
    user_id = await get_current_user_id(request)
    return await AsyncUsersODM.get_current_user_response(user_id)


@router.post("")
@permission_required(Permissions.ADMIN)
async def create_user(request: Request, json: CreateUserSchema):
    password = json.password or generate_password()
    username = json.username or f"{json.last_name.lower()}_{json.name.lower()}"

    user = await AsyncUsersODM.insert_user(
        username=username,
        password=password,
        name=json.name,
        last_name=json.last_name,
        permissions=json.permissions,
        group_id=json.group_id,
    )

    return await AsyncUsersODM.to_created_response(
        user=user,
        temporary_password=password if json.password is None else None,
    )


@router.get("")
@permission_required(Permissions.ADMIN)
async def get_users(
    request: Request,
    permissions: Optional[Permissions] = None,
    group_id: Optional[PydanticObjectId] = None,
):
    return await AsyncUsersODM.get_all_users(
        permissions=permissions,
        group_id=group_id,
    )


@router.get("/{user_id}")
@permission_required(Permissions.ADMIN)
async def get_user(request: Request, user_id: str):
    user = await AsyncUsersODM.get_user_by_id(user_id)
    return await AsyncUsersODM.to_user_response(user)


@router.put("/{user_id}")
@permission_required(Permissions.ADMIN)
async def update_user(request: Request, user_id: str, json: UpdateUserSchema):
    user = await AsyncUsersODM.update_user(
        user_id=user_id,
        username=json.username,
        password=json.password,
        name=json.name,
        last_name=json.last_name,
        permissions=json.permissions,
        group_id=json.group_id,
    )

    return await AsyncUsersODM.to_user_response(user)


@router.delete("/{user_id}")
@permission_required(Permissions.ADMIN)
async def delete_user(request: Request, user_id: str):
    await AsyncUsersODM.delete_user(user_id=user_id)

    return {"detail": "Пользователь удалён"}