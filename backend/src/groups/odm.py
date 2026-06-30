import re
import secrets
import string
from typing import Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from src.groups.documents import GroupsDocument
from src.groups.schemas import (
    BulkStudentCreateSchema,
    CreatedBulkStudentSchema,
    GroupResponseSchema,
)
from src.users.documents import Permissions, UsersDocument
from src.users.odm import AsyncUsersODM, parse_object_id


CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def transliterate(value: str) -> str:
    result = []

    for char in value.lower():
        result.append(CYRILLIC_TO_LATIN.get(char, char))

    return "".join(result)


def slugify(value: str) -> str:
    value = transliterate(value)
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def generate_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def generate_unique_username(
    group_name: str,
    name: str,
    last_name: str,
) -> str:
    base_username = slugify(f"{group_name}_{last_name}_{name}")

    if not base_username:
        base_username = f"student_{secrets.token_hex(4)}"

    username = base_username
    counter = 2

    while await UsersDocument.find_one(UsersDocument.username == username):
        username = f"{base_username}_{counter}"
        counter += 1

    return username


class AsyncGroupsODM:
    @staticmethod
    async def create_group(name: str) -> GroupsDocument:
        existing_group = await GroupsDocument.find_one(GroupsDocument.name == name)

        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Группа с таким названием уже существует",
            )

        group = GroupsDocument(name=name)
        await group.insert()

        return group

    @staticmethod
    async def get_group_by_id(group_id: str | PydanticObjectId) -> GroupsDocument:
        if not isinstance(group_id, PydanticObjectId):
            group_id = parse_object_id(str(group_id), "Неверный id группы")

        group = await GroupsDocument.find_one(GroupsDocument.id == group_id)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Группа не найдена",
            )

        return group

    @staticmethod
    async def get_all_groups() -> list[GroupResponseSchema]:
        groups = await GroupsDocument.find_all().to_list()

        return [
            GroupResponseSchema(
                id=group.id,
                name=group.name,
            )
            for group in groups
        ]

    @staticmethod
    async def update_group(
        group_id: str,
        name: Optional[str] = None,
    ) -> GroupsDocument:
        group = await AsyncGroupsODM.get_group_by_id(group_id)

        if name and name != group.name:
            existing_group = await GroupsDocument.find_one(GroupsDocument.name == name)

            if existing_group:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Группа с таким названием уже существует",
                )

            group.name = name

        await group.save()
        return group

    @staticmethod
    async def delete_group(group_id: str) -> None:
        group = await AsyncGroupsODM.get_group_by_id(group_id)

        students_count = await UsersDocument.find(
            UsersDocument.group_id == group.id,
            UsersDocument.permissions == Permissions.STUDENT,
        ).count()

        if students_count > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя удалить группу, в которой есть студенты",
            )

        await group.delete()

    @staticmethod
    async def to_group_response(group: GroupsDocument) -> GroupResponseSchema:
        return GroupResponseSchema(
            id=group.id,
            name=group.name,
        )

    @staticmethod
    async def get_group_students(group_id: str) -> list:
        group = await AsyncGroupsODM.get_group_by_id(group_id)

        students = await UsersDocument.find(
            UsersDocument.group_id == group.id,
            UsersDocument.permissions == Permissions.STUDENT,
        ).to_list()

        return [
            {
                "id": student.id,
                "username": student.username,
                "name": student.name,
                "last_name": student.last_name,
                "permissions": student.permissions,
                "group_id": student.group_id,
            }
            for student in students
        ]

    @staticmethod
    async def add_student_to_group(
        group_id: str,
        student_id: PydanticObjectId,
    ) -> UsersDocument:
        group = await AsyncGroupsODM.get_group_by_id(group_id)
        student = await AsyncUsersODM.get_user_by_id(student_id)

        if student.permissions != Permissions.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="В группу можно добавить только студента",
            )

        student.group_id = group.id
        await student.save()

        return student

    @staticmethod
    async def remove_student_from_group(
        group_id: str,
        student_id: str,
    ) -> UsersDocument:
        group = await AsyncGroupsODM.get_group_by_id(group_id)
        student = await AsyncUsersODM.get_user_by_id(student_id)

        if student.permissions != Permissions.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Из группы можно удалить только студента",
            )

        if student.group_id != group.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Студент не состоит в этой группе",
            )

        student.group_id = None
        await student.save()

        return student

    @staticmethod
    async def bulk_create_students(
        group_id: str,
        students: list[BulkStudentCreateSchema],
    ) -> list[CreatedBulkStudentSchema]:
        group = await AsyncGroupsODM.get_group_by_id(group_id)

        created_students = []

        for student_data in students:
            username = await generate_unique_username(
                group_name=group.name,
                name=student_data.name,
                last_name=student_data.last_name,
            )

            password = generate_password()

            user = await AsyncUsersODM.insert_user(
                username=username,
                password=password,
                name=student_data.name,
                last_name=student_data.last_name,
                permissions=Permissions.STUDENT,
                group_id=group.id,
            )

            created_students.append(
                CreatedBulkStudentSchema(
                    id=user.id,
                    username=user.username,
                    password=password,
                    name=user.name,
                    last_name=user.last_name,
                    group_id=group.id,
                )
            )

        return created_students