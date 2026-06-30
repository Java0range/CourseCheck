from beanie import Document

class DisciplinesDocument(Document):
    name: str
    desc: str
    class Settings:
        name = "disciplines"