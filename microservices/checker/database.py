from __future__ import annotations

import inspect
from typing import Any

from beanie import init_beanie

try:
    from pymongo import AsyncMongoClient
except ImportError:  # pragma: no cover - fallback for projects using motor
    from motor.motor_asyncio import AsyncIOMotorClient as AsyncMongoClient  # type: ignore

from models import (
    CourseOfferingsDocument,
    FilesDocument,
    SubmissionsDocument,
)
from settings import MONGO_DB_NAME, config


mongo_client: Any | None = None


async def init_worker_database() -> None:
    global mongo_client

    mongo_client = AsyncMongoClient(config.get_mongo_url())

    await init_beanie(
        database=mongo_client[MONGO_DB_NAME],
        document_models=[
            SubmissionsDocument,
            FilesDocument,
            CourseOfferingsDocument,
        ],
    )


async def close_worker_database() -> None:
    global mongo_client

    if mongo_client is None:
        return

    close_result = mongo_client.close()
    if inspect.isawaitable(close_result):
        await close_result

    mongo_client = None
