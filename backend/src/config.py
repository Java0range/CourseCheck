from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent


class Config(BaseSettings):
    SECRET_TOKEN: SecretStr
    MONGO_USER: SecretStr
    MONGO_PASSWORD: SecretStr
    MONGO_HOST: SecretStr
    MONGO_PORT: SecretStr
    RABBIT_MQ_USER: SecretStr
    RABBIT_MQ_PASSWORD: SecretStr
    RABBIT_MQ_HOST: SecretStr
    RABBIT_MQ_PORT: SecretStr


    def get_mongo_url(self):
        mongo_user = self.MONGO_USER.get_secret_value()
        mongo_password = self.MONGO_PASSWORD.get_secret_value()
        mongo_host = self.MONGO_HOST.get_secret_value()
        mongo_port = self.MONGO_PORT.get_secret_value()
        return f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"


    def get_rabbitmq_url(self):
        rabbitmq_user = self.RABBIT_MQ_USER.get_secret_value()
        rabbitmq_password = self.RABBIT_MQ_PASSWORD.get_secret_value()
        rabbitmq_host = self.RABBIT_MQ_HOST.get_secret_value()
        rabbitmq_port = self.RABBIT_MQ_PORT.get_secret_value()
        return f"amqp://{rabbitmq_user}:{rabbitmq_password}@{rabbitmq_host}:{rabbitmq_port}/"


    def get_secret_token(self):
        return self.SECRET_TOKEN.get_secret_value()


    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / "src" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = Config()