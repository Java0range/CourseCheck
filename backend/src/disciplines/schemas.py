from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel


class CreateDisciplineSchema(BaseModel):
    name: str
    desc: str = ""


class UpdateDisciplineSchema(BaseModel):
    name: Optional[str] = None
    desc: Optional[str] = None


class DisciplineResponseSchema(BaseModel):
    id: PydanticObjectId
    name: str
    desc: str