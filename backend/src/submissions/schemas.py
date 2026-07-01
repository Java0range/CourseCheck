from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel

from src.submissions.documents import SubmissionStatus


class ReviewSubmissionSchema(BaseModel):
    status: SubmissionStatus
    teacher_comment: Optional[str] = None


class SubmissionResponseSchema(BaseModel):
    id: PydanticObjectId

    course_offering_id: PydanticObjectId

    student_id: PydanticObjectId
    group_id: PydanticObjectId
    discipline_id: PydanticObjectId
    teacher_id: PydanticObjectId

    file_id: PydanticObjectId

    attempt_no: int
    status: SubmissionStatus

    student_comment: Optional[str] = None

    teacher_comment: Optional[str] = None
    reviewed_by: Optional[PydanticObjectId] = None
    reviewed_at: Optional[datetime] = None

    submitted_at: datetime
    updated_at: datetime


class SubmissionFullResponseSchema(SubmissionResponseSchema):
    student_name: Optional[str] = None
    student_last_name: Optional[str] = None

    teacher_name: Optional[str] = None
    teacher_last_name: Optional[str] = None

    file_original_name: Optional[str] = None
    file_size: Optional[int] = None
    file_content_type: Optional[str] = None

    coursework_title: Optional[str] = None