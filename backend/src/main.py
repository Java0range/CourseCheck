from contextlib import asynccontextmanager
from uvicorn import run as uvicorn_run
from beanie import init_beanie
from pymongo import AsyncMongoClient
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.config import config
from src.queries.odm import AsyncODM
from src.users.documents import UsersDocument


from src.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(config.get_mongo_url())
    await init_beanie(database=client.CourseCheck, document_models=[UsersDocument])
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
    return app


fastapi_app = create_fastapi_app()


if __name__ == "__main__":
    uvicorn_run("src.main:fastapi_app", host="0.0.0.0", port=8000)