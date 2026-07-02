from pathlib import Path

from beanie import PydanticObjectId

from models import (
    CourseOfferingsDocument,
    FilesDocument,
    SubmissionsDocument,
)
from settings import FILES_BASE_DIR


def parse_object_id(value: str, field_name: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except Exception as exc:
        raise RuntimeError(f"Некорректный {field_name}: {value}") from exc


async def get_submission_by_id(submission_id: str) -> SubmissionsDocument:
    object_id = parse_object_id(submission_id, "submission_id")
    submission = await SubmissionsDocument.get(object_id)

    if submission is None:
        raise RuntimeError(f"Сдача не найдена: {submission_id}")

    return submission


async def get_file_by_id(file_id: PydanticObjectId) -> FilesDocument:
    file_document = await FilesDocument.get(file_id)

    if file_document is None:
        raise RuntimeError(f"Файл не найден: {file_id}")

    return file_document


async def get_course_offering_by_id(
    course_offering_id: PydanticObjectId,
) -> CourseOfferingsDocument:
    course_offering = await CourseOfferingsDocument.get(course_offering_id)

    if course_offering is None:
        raise RuntimeError(f"Курсовая не найдена: {course_offering_id}")

    return course_offering


def resolve_local_file_path(file_document: FilesDocument) -> Path:
    """
    Resolves the file path stored by the API.

    The API stores paths in FilesDocument.path. In the provided code these paths
    are relative, for example uploads/courseworks/<stored_name>.docx. Because
    the worker can run from a different directory, this function tries both the
    raw path and FILES_BASE_DIR / path.
    """

    raw_path = Path(file_document.path)

    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.append(raw_path)
        candidates.append(FILES_BASE_DIR / raw_path)
        candidates.append(FILES_BASE_DIR / file_document.stored_name)
        candidates.append(FILES_BASE_DIR / "uploads" / "courseworks" / file_document.stored_name)

    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate.exists() and candidate.is_file():
            return candidate

    checked = "\n".join(f"- {candidate.resolve()}" for candidate in candidates)
    raise RuntimeError(
        "Файл сдачи есть в MongoDB, но отсутствует на диске. "
        f"file_id={file_document.id}, stored_name={file_document.stored_name}. "
        "Проверь общий volume между API и worker. Проверенные пути:\n"
        f"{checked}"
    )


async def get_submission_check_context(
    submission: SubmissionsDocument,
) -> tuple[Path, str, str]:
    file_document = await get_file_by_id(submission.file_id)
    course_offering = await get_course_offering_by_id(submission.course_offering_id)

    file_path = resolve_local_file_path(file_document)
    topic = course_offering.coursework_title.strip()
    description = course_offering.coursework_desc.strip()

    if not topic:
        raise RuntimeError(
            f"У курсовой {course_offering.id} пустая тема coursework_title"
        )

    return file_path, topic, description
