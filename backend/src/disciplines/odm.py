from typing import Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from src.disciplines.documents import DisciplinesDocument
from src.disciplines.schemas import DisciplineResponseSchema
from src.users.odm import parse_object_id


class AsyncDisciplinesODM:
    @staticmethod
    async def create_discipline(name: str, desc: str = "") -> DisciplinesDocument:
        existing_discipline = await DisciplinesDocument.find_one(
            DisciplinesDocument.name == name
        )

        if existing_discipline:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Дисциплина с таким названием уже существует",
            )

        discipline = DisciplinesDocument(
            name=name,
            desc=desc,
        )

        await discipline.insert()
        return discipline

    @staticmethod
    async def get_discipline_by_id(
        discipline_id: str | PydanticObjectId,
    ) -> DisciplinesDocument:
        if not isinstance(discipline_id, PydanticObjectId):
            discipline_id = parse_object_id(
                str(discipline_id),
                "Неверный id дисциплины",
            )

        discipline = await DisciplinesDocument.find_one(
            DisciplinesDocument.id == discipline_id
        )

        if not discipline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Дисциплина не найдена",
            )

        return discipline

    @staticmethod
    async def get_all_disciplines(
        search: Optional[str] = None,
    ) -> list[DisciplineResponseSchema]:
        query = {}

        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        disciplines = await DisciplinesDocument.find(query).to_list()

        return [
            DisciplineResponseSchema(
                id=discipline.id,
                name=discipline.name,
                desc=discipline.desc,
            )
            for discipline in disciplines
        ]

    @staticmethod
    async def update_discipline(
        discipline_id: str,
        name: Optional[str] = None,
        desc: Optional[str] = None,
    ) -> DisciplinesDocument:
        discipline = await AsyncDisciplinesODM.get_discipline_by_id(discipline_id)

        if name and name != discipline.name:
            existing_discipline = await DisciplinesDocument.find_one(
                DisciplinesDocument.name == name
            )

            if existing_discipline:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Дисциплина с таким названием уже существует",
                )

            discipline.name = name

        if desc is not None:
            discipline.desc = desc

        await discipline.save()
        return discipline

    @staticmethod
    async def delete_discipline(discipline_id: str) -> None:
        discipline = await AsyncDisciplinesODM.get_discipline_by_id(discipline_id)
        await discipline.delete()

    @staticmethod
    async def to_discipline_response(
        discipline: DisciplinesDocument,
    ) -> DisciplineResponseSchema:
        return DisciplineResponseSchema(
            id=discipline.id,
            name=discipline.name,
            desc=discipline.desc,
        )