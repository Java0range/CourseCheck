from typing import Optional

from fastapi import APIRouter, Request

from src.disciplines.odm import AsyncDisciplinesODM
from src.disciplines.schemas import CreateDisciplineSchema, UpdateDisciplineSchema
from src.users.documents import Permissions
from src.users.utils import permission_required


router = APIRouter(prefix="/disciplines", tags=["Disciplines"])


@router.post("")
@permission_required(Permissions.ADMIN)
async def create_discipline(request: Request, json: CreateDisciplineSchema):
    discipline = await AsyncDisciplinesODM.create_discipline(
        name=json.name,
        desc=json.desc,
    )

    return await AsyncDisciplinesODM.to_discipline_response(discipline)


@router.get("")
@permission_required(Permissions.STUDENT)
async def get_disciplines(
    request: Request,
    search: Optional[str] = None,
):
    return await AsyncDisciplinesODM.get_all_disciplines(search=search)


@router.get("/{discipline_id}")
@permission_required(Permissions.STUDENT)
async def get_discipline(request: Request, discipline_id: str):
    discipline = await AsyncDisciplinesODM.get_discipline_by_id(discipline_id)
    return await AsyncDisciplinesODM.to_discipline_response(discipline)


@router.put("/{discipline_id}")
@permission_required(Permissions.ADMIN)
async def update_discipline(
    request: Request,
    discipline_id: str,
    json: UpdateDisciplineSchema,
):
    discipline = await AsyncDisciplinesODM.update_discipline(
        discipline_id=discipline_id,
        name=json.name,
        desc=json.desc,
    )

    return await AsyncDisciplinesODM.to_discipline_response(discipline)


@router.delete("/{discipline_id}")
@permission_required(Permissions.ADMIN)
async def delete_discipline(request: Request, discipline_id: str):
    await AsyncDisciplinesODM.delete_discipline(discipline_id=discipline_id)

    return {"detail": "Дисциплина удалена"}