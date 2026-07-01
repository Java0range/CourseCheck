from src.users.documents import Permissions, UsersDocument
from src.users.odm import AsyncUsersODM


class AsyncODM:
    @staticmethod
    async def insert_root():
        root = await UsersDocument.find_one(UsersDocument.username == "root")

        if root:
            return

        await AsyncUsersODM.insert_user(
            username="root",
            password="toor",
            name="Root",
            last_name="Admin",
            permissions=Permissions.ADMIN,
            group_id=None,
        )