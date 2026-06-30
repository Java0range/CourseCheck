from src.users.odm import AsyncUsersODM


class AsyncODM:
    @staticmethod
    async def insert_root():
        await AsyncUsersODM.insert_user(
            username="root",
            password="toor",
            permissions="ADMIN"
        )
        await AsyncUsersODM.insert_user(
            username="user",
            password="user",
            permissions="USER"
        )