from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SubmissionStatus(str, Enum):
    SUBMITTED = "submitted"
    CREDITED = "credited"
    NOT_CREDITED = "not_credited"


class SubmissionsDocument(Document):
    course_offering_id: PydanticObjectId

    student_id: PydanticObjectId
    group_id: PydanticObjectId
    discipline_id: PydanticObjectId
    teacher_id: PydanticObjectId

    file_id: PydanticObjectId

    attempt_no: int = 1

    status: SubmissionStatus = SubmissionStatus.SUBMITTED

    student_comment: Optional[str] = None

    teacher_comment: Optional[str] = None
    reviewed_by: Optional[PydanticObjectId] = None
    reviewed_at: Optional[datetime] = None

    submitted_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "submissions"
        indexes = [
            IndexModel(
                [
                    ("course_offering_id", ASCENDING),
                    ("student_id", ASCENDING),
                    ("attempt_no", ASCENDING),
                ],
                unique=True,
            ),
            IndexModel([("course_offering_id", ASCENDING)]),
            IndexModel([("student_id", ASCENDING), ("submitted_at", DESCENDING)]),
            IndexModel([("group_id", ASCENDING)]),
            IndexModel([("discipline_id", ASCENDING)]),
            IndexModel([("teacher_id", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("submitted_at", DESCENDING)]),
        ]