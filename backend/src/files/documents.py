from datetime import datetime, timezone
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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