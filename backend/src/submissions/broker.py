from datetime import datetime, timezone

from src.config import config

from faststream.rabbit import RabbitBroker

from src.submissions.schemas import SubmissionCheckRequestedMessage


SUBMISSION_CHECK_QUEUE = "coursework.submission.check"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def publish_submission_check_requested(submission_id: str) -> None:
    """
    Публикует задачу проверки в RabbitMQ через FastStream.

    Это простой вариант без внедрения брокера в lifespan FastAPI-приложения:
    соединение открывается только на время публикации. Если у тебя уже есть
    общий broker в main.py, можно заменить эту функцию на использование
    глобального подключённого RabbitBroker.
    """
    message = SubmissionCheckRequestedMessage(
        submission_id=submission_id,
        requested_at=utc_now(),
    )

    broker = RabbitBroker(config.get_rabbitmq_url())
    async with broker:
        await broker.publish(
            message.model_dump(mode="json"),
            SUBMISSION_CHECK_QUEUE,
        )
