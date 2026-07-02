from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from faststream import FastStream
from faststream.rabbit import RabbitBroker

from checker import check_coursework
from database import close_worker_database, init_worker_database
from models import (
    FINAL_TEACHER_STATUSES,
    SubmissionStatus,
    SubmissionsDocument,
    utc_now,
)
from schemas import SubmissionCheckRequestedMessage
from settings import SUBMISSION_CHECK_QUEUE, config
from storage import (
    get_submission_by_id,
    get_submission_check_context,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("coursework-checking-worker")

broker = RabbitBroker(config.get_rabbitmq_url())
app = FastStream(broker)


@app.on_startup
async def on_startup() -> None:
    await init_worker_database()
    logger.info("Coursework checking worker started")


@app.on_shutdown
async def on_shutdown() -> None:
    await close_worker_database()
    logger.info("Coursework checking worker stopped")


async def save_submission_safely(submission: SubmissionsDocument) -> None:
    submission.updated_at = utc_now()
    await submission.save()


async def mark_check_started(submission: SubmissionsDocument) -> SubmissionsDocument:
    """
    Marks a submission as checking unless the teacher has already reviewed it.
    """

    if submission.status not in FINAL_TEACHER_STATUSES:
        submission.status = SubmissionStatus.CHECKING

    submission.ai_error = None
    submission.ai_started_at = utc_now()
    submission.updated_at = utc_now()
    await submission.save()
    return submission


async def apply_check_result(
    submission_id: str,
    *,
    accepted: bool,
    comment: str,
) -> None:
    """
    Saves AI result.

    If a teacher has already set credited/not_credited while AI was working, the
    worker keeps the teacher's final status and only saves the AI comment.
    """

    submission = await get_submission_by_id(submission_id)
    submission.ai_comment = comment
    submission.ai_error = None
    submission.ai_checked_at = utc_now()

    if submission.status not in FINAL_TEACHER_STATUSES:
        submission.status = (
            SubmissionStatus.AI_ACCEPTED if accepted else SubmissionStatus.AI_REJECTED
        )

    await save_submission_safely(submission)


async def mark_check_failed(submission_id: str, error_message: str) -> None:
    try:
        submission = await get_submission_by_id(submission_id)
    except Exception:
        logger.exception("Cannot mark check_failed because submission was not found")
        return

    submission.ai_error = error_message
    submission.ai_checked_at = datetime.now(timezone.utc)

    if submission.status not in FINAL_TEACHER_STATUSES:
        submission.status = SubmissionStatus.CHECK_FAILED

    await save_submission_safely(submission)


@broker.subscriber(SUBMISSION_CHECK_QUEUE)
async def handle_submission_check_requested(
    message: SubmissionCheckRequestedMessage,
) -> None:
    """
    Handles one coursework checking task.

    The handler catches all errors and writes check_failed to MongoDB. This
    prevents a broken document or a temporary LM Studio problem from creating an
    endless RabbitMQ redelivery loop.
    """

    submission_id = message.submission_id
    logger.info("Received coursework check task: submission_id=%s", submission_id)

    try:
        submission = await get_submission_by_id(submission_id)
        submission = await mark_check_started(submission)

        file_path, topic, coursework_desc = await get_submission_check_context(submission)

        logger.info(
            "Checking coursework: submission_id=%s file_path=%s topic=%s",
            submission_id,
            file_path,
            topic,
        )

        result = await check_coursework(
            file_path=file_path,
            topic=topic,
            coursework_desc=coursework_desc,
        )

        await apply_check_result(
            submission_id,
            accepted=result.accepted,
            comment=result.comment,
        )

        logger.info(
            "Coursework check finished: submission_id=%s accepted=%s",
            submission_id,
            result.accepted,
        )
    except Exception as exc:
        logger.exception("Coursework check failed: submission_id=%s", submission_id)
        await mark_check_failed(submission_id, str(exc))


async def main() -> None:
    await app.run(log_level=logging.INFO)


if __name__ == "__main__":
    asyncio.run(main())