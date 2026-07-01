from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CourseOfferingStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CourseOfferingsDocument(Document):
    discipline_id: PydanticObjectId
    group_id: PydanticObjectId
    teacher_id: PydanticObjectId

    coursework_title: str
    coursework_desc: str = ""

    deadline_at: Optional[datetime] = None

    status: CourseOfferingStatus = CourseOfferingStatus.ACTIVE

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "course_offerings"
        indexes = [
            IndexModel(
                [
                    ("discipline_id", ASCENDING),
                    ("group_id", ASCENDING),
                ],
                unique=True,
            ),
            IndexModel([("teacher_id", ASCENDING)]),
            IndexModel([("group_id", ASCENDING)]),
            IndexModel([("discipline_id", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
        ]