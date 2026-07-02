from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from starlette.middleware.cors import CORSMiddleware
from uvicorn import run as uvicorn_run

from src.config import config

from src.course_offerings.documents import CourseOfferingsDocument
from src.course_offerings.router import router as course_offerings_router

from src.disciplines.documents import DisciplinesDocument
from src.disciplines.router import router as disciplines_router

from src.files.documents import FilesDocument
from src.files.router import router as files_router

from src.groups.documents import GroupsDocument
from src.groups.router import router as groups_router

from src.submissions.documents import SubmissionsDocument
from src.submissions.router import router as submissions_router

from src.users.documents import UsersDocument
from src.users.router import router as users_router

from src.queries.odm import AsyncODM


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(config.get_mongo_url())

    await init_beanie(
        database=client.CourseCheck,
        document_models=[
            UsersDocument,
            GroupsDocument,
            DisciplinesDocument,
            CourseOfferingsDocument,
            FilesDocument,
            SubmissionsDocument,
        ],
    )

    # await AsyncODM.insert_root()

    yield


def create_fastapi_app():
    app = FastAPI(lifespan=lifespan)
    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    app.include_router(users_router)
    app.include_router(groups_router)
    app.include_router(disciplines_router)
    app.include_router(course_offerings_router)
    app.include_router(files_router)
    app.include_router(submissions_router)


    return app


fastapi_app = create_fastapi_app()


if __name__ == "__main__":
    uvicorn_run("src.main:fastapi_app", host="0.0.0.0", port=8000)