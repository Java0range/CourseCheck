from pathlib import Path
from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).parent


# =========================
# Shared database / broker
# =========================


MONGO_DB_NAME = "CourseCheck"

# Queue name must match the publisher in the API service.
SUBMISSION_CHECK_QUEUE = "coursework.submission.check"


# =========================
# File storage
# =========================

FILES_BASE_DIR = Path(r"C:\CourseCheck\backend\src\uploads\courseworks")


# =========================
# LM Studio
# =========================

LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
LMSTUDIO_API_KEY = "lm-studio"

# Put here the exact model id from LM Studio.
LMSTUDIO_MODEL = "qwen/qwen3-8b"

REQUEST_TIMEOUT_SECONDS = 840.0
TEMPERATURE = 0.1
MAX_COMPLETION_TOKENS = 3000
MAX_PROMPT_CHARS = 120_000


# =========================
# Document checking
# =========================

SUBMITTED_MARKER = "{[submitted]}"

SKIP_BEFORE_MAIN_CONTENT = True
MAIN_CONTENT_START_PATTERNS = (
    r"^ВВЕДЕНИЕ$",
    r"^ГЛАВА\s+\d+",
    r"^РАЗДЕЛ\s+\d+",
    r"^\d+\.\s+\S+",
)

FORMATTING_REQUIREMENTS = """
1. Шрифт основного текста: Times New Roman, размер 14.
2. Межстрочный интервал: 1.5 (Полуторный).
3. Выравнивание основного текста: По ширине (Justify).
4. Абзацный отступ (Красная строка): 1.25 см.
5. Заголовки глав: Шрифт Times New Roman, размер 14, Выравнивание по центру.
6. Все остальные заголовки: Шрифт Times New Roman, размер 14, Выравнивание по левому краю.
7. После заголовка глав должна быть пустая строка.
8. Перед и после всех остальных заголовков должна быть пустая строка.
""".strip()


class WorkerConfig(BaseSettings):
    """
    Independent worker config.

    The names match the main API .env fields, but this module does not import
    src.config. You can either copy the same .env next to the worker or export
    these variables in the worker environment.
    """

    MONGO_URL: Optional[SecretStr] = None
    MONGO_USER: Optional[SecretStr] = None
    MONGO_PASSWORD: Optional[SecretStr] = None
    MONGO_HOST: Optional[SecretStr] = None
    MONGO_PORT: Optional[SecretStr] = None

    RABBITMQ_URL: Optional[SecretStr] = None
    RABBIT_MQ_USER: Optional[SecretStr] = None
    RABBIT_MQ_PASSWORD: Optional[SecretStr] = None
    RABBIT_MQ_HOST: Optional[SecretStr] = None
    RABBIT_MQ_PORT: Optional[SecretStr] = None

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", ROOT_DIR / "src" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_mongo_url(self) -> str:
        if self.MONGO_URL is not None:
            return self.MONGO_URL.get_secret_value()

        required = {
            "MONGO_USER": self.MONGO_USER,
            "MONGO_PASSWORD": self.MONGO_PASSWORD,
            "MONGO_HOST": self.MONGO_HOST,
            "MONGO_PORT": self.MONGO_PORT,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise RuntimeError(
                "Не заданы настройки MongoDB для микросервиса: "
                + ", ".join(missing)
                + ". Либо задай MONGO_URL, либо те же MONGO_* переменные, что в API."
            )

        user = self.MONGO_USER.get_secret_value()
        password = self.MONGO_PASSWORD.get_secret_value()
        host = self.MONGO_HOST.get_secret_value()
        port = self.MONGO_PORT.get_secret_value()
        return f"mongodb://{user}:{password}@{host}:{port}/"

    def get_rabbitmq_url(self) -> str:
        if self.RABBITMQ_URL is not None:
            return self.RABBITMQ_URL.get_secret_value()

        required = {
            "RABBIT_MQ_USER": self.RABBIT_MQ_USER,
            "RABBIT_MQ_PASSWORD": self.RABBIT_MQ_PASSWORD,
            "RABBIT_MQ_HOST": self.RABBIT_MQ_HOST,
            "RABBIT_MQ_PORT": self.RABBIT_MQ_PORT,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise RuntimeError(
                "Не заданы настройки RabbitMQ для микросервиса: "
                + ", ".join(missing)
                + ". Либо задай RABBITMQ_URL, либо те же RABBIT_MQ_* переменные, что в API."
            )

        user = self.RABBIT_MQ_USER.get_secret_value()  # type: ignore[union-attr]
        password = self.RABBIT_MQ_PASSWORD.get_secret_value()  # type: ignore[union-attr]
        host = self.RABBIT_MQ_HOST.get_secret_value()  # type: ignore[union-attr]
        port = self.RABBIT_MQ_PORT.get_secret_value()  # type: ignore[union-attr]
        return f"amqp://{user}:{password}@{host}:{port}/"


config = WorkerConfig()
