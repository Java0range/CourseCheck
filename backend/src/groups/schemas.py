from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel


class CreateGroupSchema(BaseModel):
    name: str


class UpdateGroupSchema(BaseModel):
    name: Optional[str] = None


class GroupResponseSchema(BaseModel):
    id: PydanticObjectId
    name: str


class AddStudentToGroupSchema(BaseModel):
    student_id: PydanticObjectId


class BulkStudentCreateSchema(BaseModel):
    name: str
    last_name: str


class BulkCreateStudentsSchema(BaseModel):
    students: list[BulkStudentCreateSchema]


class CreatedBulkStudentSchema(BaseModel):
    id: PydanticObjectId
    username: str
    password: str
    name: str
    last_name: str
    group_id: PydanticObjectId


class BulkCreateStudentsResponseSchema(BaseModel):
    group: GroupResponseSchema
    created: list[CreatedBulkStudentSchema]