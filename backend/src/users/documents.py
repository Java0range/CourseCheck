from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pymongo import IndexModel, ASCENDING


class Permissions(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class UsersDocument(Document):
    username: str
    password: str

    name: str
    last_name: str

    permissions: Permissions

    group_id: Optional[PydanticObjectId] = None

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("username", ASCENDING)], unique=True),
            IndexModel([("permissions", ASCENDING)]),
            IndexModel([("group_id", ASCENDING)]),
        ]