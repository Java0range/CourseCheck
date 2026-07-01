from beanie import Document
from pymongo import ASCENDING, IndexModel


class DisciplinesDocument(Document):
    name: str
    desc: str = ""

    class Settings:
        name = "disciplines"
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True),
        ]