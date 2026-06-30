from fastapi import APIRouter, Request

from src.groups.odm import AsyncGroupsODM
from src.groups.schemas import (
    AddStudentToGroupSchema,
    BulkCreateStudentsResponseSchema,
    BulkCreateStudentsSchema,
    CreateGroupSchema,
    UpdateGroupSchema,
)
from src.users.documents import Permissions
from src.users.odm import AsyncUsersODM
from src.users.utils import permission_required


router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("")
@permission_required(Permissions.ADMIN)
async def create_group(request: Request, json: CreateGroupSchema):
    group = await AsyncGroupsODM.create_group(name=json.name)
    return await AsyncGroupsODM.to_group_response(group)


@router.get("")
@permission_required(Permissions.ADMIN)
async def get_groups(request: Request):
    return await AsyncGroupsODM.get_all_groups()


@router.get("/{group_id}")
@permission_required(Permissions.ADMIN)
async def get_group(request: Request, group_id: str):
    group = await AsyncGroupsODM.get_group_by_id(group_id)
    return await AsyncGroupsODM.to_group_response(group)


@router.put("/{group_id}")
@permission_required(Permissions.ADMIN)
async def update_group(request: Request, group_id: str, json: UpdateGroupSchema):
    group = await AsyncGroupsODM.update_group(
        group_id=group_id,
        name=json.name,
    )

    return await AsyncGroupsODM.to_group_response(group)


@router.delete("/{group_id}")
@permission_required(Permissions.ADMIN)
async def delete_group(request: Request, group_id: str):
    await AsyncGroupsODM.delete_group(group_id=group_id)
    return {"detail": "Группа удалена"}


@router.get("/{group_id}/students")
@permission_required(Permissions.ADMIN)
async def get_group_students(request: Request, group_id: str):
    return await AsyncGroupsODM.get_group_students(group_id=group_id)


@router.post("/{group_id}/students")
@permission_required(Permissions.ADMIN)
async def add_student_to_group(
    request: Request,
    group_id: str,
    json: AddStudentToGroupSchema,
):
    student = await AsyncGroupsODM.add_student_to_group(
        group_id=group_id,
        student_id=json.student_id,
    )

    return await AsyncUsersODM.to_user_response(student)


@router.delete("/{group_id}/students/{student_id}")
@permission_required(Permissions.ADMIN)
async def remove_student_from_group(
    request: Request,
    group_id: str,
    student_id: str,
):
    student = await AsyncGroupsODM.remove_student_from_group(
        group_id=group_id,
        student_id=student_id,
    )

    return await AsyncUsersODM.to_user_response(student)


@router.post("/{group_id}/students/bulk")
@permission_required(Permissions.ADMIN)
async def bulk_create_students(
    request: Request,
    group_id: str,
    json: BulkCreateStudentsSchema,
):
    group = await AsyncGroupsODM.get_group_by_id(group_id)

    created_students = await AsyncGroupsODM.bulk_create_students(
        group_id=group_id,
        students=json.students,
    )

    return BulkCreateStudentsResponseSchema(
        group=await AsyncGroupsODM.to_group_response(group),
        created=created_students,
    )