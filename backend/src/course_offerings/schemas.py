from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel

from src.course_offerings.documents import CourseOfferingStatus


class CreateCourseOfferingSchema(BaseModel):
    discipline_id: PydanticObjectId
    group_id: PydanticObjectId
    teacher_id: PydanticObjectId

    coursework_title: str
    coursework_desc: str = ""

    deadline_at: Optional[datetime] = None


class UpdateCourseOfferingSchema(BaseModel):
    teacher_id: Optional[PydanticObjectId] = None

    coursework_title: Optional[str] = None
    coursework_desc: Optional[str] = None

    deadline_at: Optional[datetime] = None
    status: Optional[CourseOfferingStatus] = None


class CourseOfferingResponseSchema(BaseModel):
    id: PydanticObjectId

    discipline_id: PydanticObjectId
    group_id: PydanticObjectId
    teacher_id: PydanticObjectId

    coursework_title: str
    coursework_desc: str

    deadline_at: Optional[datetime] = None

    status: CourseOfferingStatus

    created_at: datetime
    updated_at: datetime


class CourseOfferingFullResponseSchema(CourseOfferingResponseSchema):
    discipline_name: Optional[str] = None
    group_name: Optional[str] = None
    teacher_name: Optional[str] = None
    teacher_last_name: Optional[str] = None


class AnalyticsStudentSchema(BaseModel):
    id: PydanticObjectId
    username: str
    name: str
    last_name: str


class CourseOfferingAnalyticsSchema(BaseModel):
    course_offering_id: PydanticObjectId

    coursework_title: str

    discipline_id: PydanticObjectId
    discipline_name: Optional[str] = None

    group_id: PydanticObjectId
    group_name: Optional[str] = None

    teacher_id: PydanticObjectId

    total_students: int

    submitted_students_count: int
    not_submitted_students_count: int

    credited_count: int
    not_credited_count: int
    waiting_review_count: int

    submitted_count_total: int

    submission_percent: float
    credited_percent: float

    not_submitted_students: list[AnalyticsStudentSchema]