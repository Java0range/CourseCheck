from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SubmissionStatus(str, Enum):
    """
    Local copy of the submission status enum.

    The collection is shared with the API, but the worker is a separate service,
    so it keeps its own enum instead of importing src.submissions.documents.
    """

    SUBMITTED = "submitted"
    ACCEPTED_FOR_CHECKING = "accepted_for_checking"
    CHECKING = "checking"
    AI_ACCEPTED = "ai_accepted"
    AI_REJECTED = "ai_rejected"
    CHECK_FAILED = "check_failed"
    CREDITED = "credited"
    NOT_CREDITED = "not_credited"


FINAL_TEACHER_STATUSES = {
    SubmissionStatus.CREDITED,
    SubmissionStatus.NOT_CREDITED,
}


class SubmissionsDocument(Document):
    course_offering_id: PydanticObjectId

    student_id: PydanticObjectId
    group_id: PydanticObjectId
    discipline_id: PydanticObjectId
    teacher_id: PydanticObjectId

    file_id: PydanticObjectId

    attempt_no: int = 1

    status: SubmissionStatus = SubmissionStatus.ACCEPTED_FOR_CHECKING

    student_comment: Optional[str] = None

    ai_comment: Optional[str] = None
    ai_error: Optional[str] = None
    ai_started_at: Optional[datetime] = None
    ai_checked_at: Optional[datetime] = None

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


class FilesDocument(Document):
    owner_id: PydanticObjectId

    original_name: str
    stored_name: str
    path: str

    content_type: Optional[str] = None
    size: int = 0

    uploaded_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "files"
        indexes = [
            IndexModel([("owner_id", ASCENDING), ("uploaded_at", DESCENDING)]),
            IndexModel([("stored_name", ASCENDING)], unique=True),
        ]


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
