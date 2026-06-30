from beanie import Document
from pymongo import ASCENDING, IndexModel


class GroupsDocument(Document):
    name: str

    class Settings:
        name = "groups"
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True),
        ]