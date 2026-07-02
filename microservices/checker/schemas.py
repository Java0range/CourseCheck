from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SubmissionCheckRequestedMessage(BaseModel):
    """
    RabbitMQ message contract between the API and the worker.

    Only submission_id is required. The worker reads file_id and
    course_offering_id from MongoDB so the API does not have to duplicate data
    in the message.
    """

    submission_id: str
    requested_at: datetime = Field(default_factory=utc_now)


class CourseworkCheckResult(BaseModel):
    accepted: bool
    comment: str
