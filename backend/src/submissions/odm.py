from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, UploadFile, status

from src.course_offerings.documents import CourseOfferingStatus
from src.course_offerings.odm import AsyncCourseOfferingsODM
from src.files.odm import AsyncFilesODM
from src.submissions.documents import SubmissionStatus, SubmissionsDocument
from src.submissions.schemas import SubmissionFullResponseSchema, SubmissionResponseSchema
from src.users.documents import Permissions, UsersDocument
from src.users.odm import AsyncUsersODM, parse_object_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AsyncSubmissionsODM:
    @staticmethod
    async def create_submission(
        course_offering_id: str,
        current_user: UsersDocument,
        file: UploadFile,
        student_comment: Optional[str] = None,
    ) -> SubmissionsDocument:
        if current_user.permissions != Permissions.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Сдавать курсовую может только студент",
            )

        if current_user.group_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Студент не состоит в группе",
            )

        course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
            course_offering_id
        )

        if course_offering.status != CourseOfferingStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Курсовая закрыта для сдачи",
            )

        if course_offering.group_id != current_user.group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Эта курсовая недоступна вашей группе",
            )

        last_submission = await SubmissionsDocument.find(
            SubmissionsDocument.course_offering_id == course_offering.id,
            SubmissionsDocument.student_id == current_user.id,
        ).sort("-attempt_no").first_or_none()

        attempt_no = 1

        if last_submission:
            attempt_no = last_submission.attempt_no + 1

        file_document = await AsyncFilesODM.save_upload_file(
            file=file,
            owner_id=current_user.id,
        )

        submission = SubmissionsDocument(
            course_offering_id=course_offering.id,
            student_id=current_user.id,
            group_id=course_offering.group_id,
            discipline_id=course_offering.discipline_id,
            teacher_id=course_offering.teacher_id,
            file_id=file_document.id,
            attempt_no=attempt_no,
            status=SubmissionStatus.SUBMITTED,
            student_comment=student_comment,
        )

        await submission.insert()
        return submission

    @staticmethod
    async def get_submission_by_id(
        submission_id: str | PydanticObjectId,
    ) -> SubmissionsDocument:
        if not isinstance(submission_id, PydanticObjectId):
            submission_id = parse_object_id(
                str(submission_id),
                "Неверный id сдачи",
            )

        submission = await SubmissionsDocument.find_one(
            SubmissionsDocument.id == submission_id
        )

        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сдача не найдена",
            )

        return submission

    @staticmethod
    async def check_submission_view_permission(
        submission: SubmissionsDocument,
        current_user: UsersDocument,
    ) -> None:
        if current_user.permissions == Permissions.ADMIN:
            return

        if (
            current_user.permissions == Permissions.TEACHER
            and submission.teacher_id == current_user.id
        ):
            return

        if (
            current_user.permissions == Permissions.STUDENT
            and submission.student_id == current_user.id
        ):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой сдаче",
        )

    @staticmethod
    async def check_submission_review_permission(
        submission: SubmissionsDocument,
        current_user: UsersDocument,
    ) -> None:
        if current_user.permissions == Permissions.ADMIN:
            return

        if (
            current_user.permissions == Permissions.TEACHER
            and submission.teacher_id == current_user.id
        ):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на проверку этой сдачи",
        )

    @staticmethod
    async def get_my_submissions(
        current_user: UsersDocument,
    ) -> list[SubmissionFullResponseSchema]:
        if current_user.permissions != Permissions.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Этот раздел доступен только студенту",
            )

        submissions = await SubmissionsDocument.find(
            SubmissionsDocument.student_id == current_user.id
        ).sort("-submitted_at").to_list()

        return [
            await AsyncSubmissionsODM.to_full_submission_response(submission)
            for submission in submissions
        ]

    @staticmethod
    async def get_student_course_offering_submissions(
        course_offering_id: str,
        current_user: UsersDocument,
    ) -> list[SubmissionFullResponseSchema]:
        if current_user.permissions != Permissions.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Этот раздел доступен только студенту",
            )

        course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
            course_offering_id
        )

        if course_offering.group_id != current_user.group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Эта курсовая недоступна вашей группе",
            )

        submissions = await SubmissionsDocument.find(
            SubmissionsDocument.course_offering_id == course_offering.id,
            SubmissionsDocument.student_id == current_user.id,
        ).sort("-attempt_no").to_list()

        return [
            await AsyncSubmissionsODM.to_full_submission_response(submission)
            for submission in submissions
        ]

    @staticmethod
    async def get_course_offering_submissions(
        course_offering_id: str,
        current_user: UsersDocument,
        status_filter: Optional[SubmissionStatus] = None,
    ) -> list[SubmissionFullResponseSchema]:
        course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
            course_offering_id
        )

        if current_user.permissions == Permissions.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Студент не может смотреть все сдачи",
            )

        if (
            current_user.permissions == Permissions.TEACHER
            and course_offering.teacher_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к сдачам этой курсовой",
            )

        query = {
            "course_offering_id": course_offering.id,
        }

        if status_filter is not None:
            query["status"] = status_filter

        submissions = await SubmissionsDocument.find(query).sort(
            "-submitted_at"
        ).to_list()

        return [
            await AsyncSubmissionsODM.to_full_submission_response(submission)
            for submission in submissions
        ]

    @staticmethod
    async def review_submission(
        submission_id: str,
        current_user: UsersDocument,
        status_value: SubmissionStatus,
        teacher_comment: Optional[str] = None,
    ) -> SubmissionsDocument:
        submission = await AsyncSubmissionsODM.get_submission_by_id(submission_id)

        await AsyncSubmissionsODM.check_submission_review_permission(
            submission=submission,
            current_user=current_user,
        )

        if status_value not in [
            SubmissionStatus.CREDITED,
            SubmissionStatus.NOT_CREDITED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Можно поставить только credited или not_credited",
            )

        submission.status = status_value
        submission.teacher_comment = teacher_comment
        submission.reviewed_by = current_user.id
        submission.reviewed_at = utc_now()
        submission.updated_at = utc_now()

        await submission.save()
        return submission

    @staticmethod
    async def to_submission_response(
        submission: SubmissionsDocument,
    ) -> SubmissionResponseSchema:
        return SubmissionResponseSchema(
            id=submission.id,
            course_offering_id=submission.course_offering_id,
            student_id=submission.student_id,
            group_id=submission.group_id,
            discipline_id=submission.discipline_id,
            teacher_id=submission.teacher_id,
            file_id=submission.file_id,
            attempt_no=submission.attempt_no,
            status=submission.status,
            student_comment=submission.student_comment,
            teacher_comment=submission.teacher_comment,
            reviewed_by=submission.reviewed_by,
            reviewed_at=submission.reviewed_at,
            submitted_at=submission.submitted_at,
            updated_at=submission.updated_at,
        )

    @staticmethod
    async def to_full_submission_response(
        submission: SubmissionsDocument,
    ) -> SubmissionFullResponseSchema:
        student_name = None
        student_last_name = None
        teacher_name = None
        teacher_last_name = None
        file_original_name = None
        file_size = None
        file_content_type = None
        coursework_title = None

        try:
            student = await AsyncUsersODM.get_user_by_id(submission.student_id)
            student_name = student.name
            student_last_name = student.last_name
        except HTTPException:
            pass

        try:
            teacher = await AsyncUsersODM.get_user_by_id(submission.teacher_id)
            teacher_name = teacher.name
            teacher_last_name = teacher.last_name
        except HTTPException:
            pass

        try:
            file_document = await AsyncFilesODM.get_file_by_id(submission.file_id)
            file_original_name = file_document.original_name
            file_size = file_document.size
            file_content_type = file_document.content_type
        except HTTPException:
            pass

        try:
            course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
                submission.course_offering_id
            )
            coursework_title = course_offering.coursework_title
        except HTTPException:
            pass

        return SubmissionFullResponseSchema(
            id=submission.id,
            course_offering_id=submission.course_offering_id,
            student_id=submission.student_id,
            group_id=submission.group_id,
            discipline_id=submission.discipline_id,
            teacher_id=submission.teacher_id,
            file_id=submission.file_id,
            attempt_no=submission.attempt_no,
            status=submission.status,
            student_comment=submission.student_comment,
            teacher_comment=submission.teacher_comment,
            reviewed_by=submission.reviewed_by,
            reviewed_at=submission.reviewed_at,
            submitted_at=submission.submitted_at,
            updated_at=submission.updated_at,
            student_name=student_name,
            student_last_name=student_last_name,
            teacher_name=teacher_name,
            teacher_last_name=teacher_last_name,
            file_original_name=file_original_name,
            file_size=file_size,
            file_content_type=file_content_type,
            coursework_title=coursework_title,
        )