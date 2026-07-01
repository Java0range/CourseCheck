from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel


class FileResponseSchema(BaseModel):
    id: PydanticObjectId

    owner_id: PydanticObjectId

    original_name: str
    stored_name: str
    path: str

    content_type: Optional[str] = None
    size: int

    uploaded_at: datetime