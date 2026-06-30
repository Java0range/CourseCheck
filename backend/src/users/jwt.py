from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from src.config import config


class Auth:
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, user_id: int) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=30)
        data = {
            "user_id": user_id,
            "type": "access",
            "exp": expire
        }
        encoded_jwt = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, user_id: int) -> str:
        expire = datetime.now(UTC) + timedelta(days=7)
        data = {
            "user_id": user_id,
            "type": "refresh",
            "exp": expire
        }
        encoded_jwt = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def check_access_token(self, access_token: str) -> str:
        try:
            payload = jwt.decode(access_token, self.secret_key, algorithms=self.algorithm)
        except JWTError:
            return "Error: Invalid access token"
        token_type: str = payload.get("type")
        if token_type != "access":
            return "Error: Invalid token type"
        expire: str = payload.get("exp")
        if (not expire) and (int(expire) < datetime.now(UTC).timestamp()):
            return "Error: Expired access token"
        user_id: int = payload.get("user_id")
        if not user_id:
            return "Error: Invalid access token"
        return str(user_id)

    def check_refresh_token(self, refresh_token: str) -> str:
        print(type(refresh_token))
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=self.algorithm)
        except JWTError:
            return "Error: Invalid refresh token"
        token_type: str = payload.get("type")
        if token_type != "refresh":
            return "Error: Invalid token type"
        expire: str = payload.get("exp")
        if (not expire) and (int(expire) < datetime.now(UTC).timestamp()):
            return "Error: Expired access token"
        user_id: int = payload.get("user_id")
        if not user_id:
            return "Error: Invalid access token"
        new_access_token: str = self.create_access_token(user_id=user_id)
        return new_access_token


security = Auth(config.get_secret_token(), "HS256")