from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from src.course_offerings.documents import (
    CourseOfferingsDocument,
    CourseOfferingStatus,
)
from src.course_offerings.schemas import (
    AnalyticsStudentSchema,
    CourseOfferingAnalyticsSchema,
    CourseOfferingFullResponseSchema,
    CourseOfferingResponseSchema,
)
from src.disciplines.odm import AsyncDisciplinesODM
from src.groups.odm import AsyncGroupsODM
from src.users.documents import Permissions, UsersDocument
from src.users.odm import AsyncUsersODM, parse_object_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AsyncCourseOfferingsODM:
    @staticmethod
    async def create_course_offering(
        discipline_id: PydanticObjectId,
        group_id: PydanticObjectId,
        teacher_id: PydanticObjectId,
        coursework_title: str,
        coursework_desc: str = "",
        deadline_at: Optional[datetime] = None,
    ) -> CourseOfferingsDocument:
        await AsyncDisciplinesODM.get_discipline_by_id(discipline_id)
        await AsyncGroupsODM.get_group_by_id(group_id)

        teacher = await AsyncUsersODM.get_user_by_id(teacher_id)

        if teacher.permissions != Permissions.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Назначенный пользователь не является преподавателем",
            )

        existing_course_offering = await CourseOfferingsDocument.find_one(
            CourseOfferingsDocument.discipline_id == discipline_id,
            CourseOfferingsDocument.group_id == group_id,
        )

        if existing_course_offering:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Для этой дисциплины и группы уже создана курсовая",
            )

        course_offering = CourseOfferingsDocument(
            discipline_id=discipline_id,
            group_id=group_id,
            teacher_id=teacher_id,
            coursework_title=coursework_title,
            coursework_desc=coursework_desc,
            deadline_at=deadline_at,
            status=CourseOfferingStatus.ACTIVE,
        )

        await course_offering.insert()
        return course_offering

    @staticmethod
    async def get_course_offering_by_id(
        course_offering_id: str | PydanticObjectId,
    ) -> CourseOfferingsDocument:
        if not isinstance(course_offering_id, PydanticObjectId):
            course_offering_id = parse_object_id(
                str(course_offering_id),
                "Неверный id курсовой",
            )

        course_offering = await CourseOfferingsDocument.find_one(
            CourseOfferingsDocument.id == course_offering_id
        )

        if not course_offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Курсовая не найдена",
            )

        return course_offering

    @staticmethod
    async def get_all_course_offerings(
        status_filter: Optional[CourseOfferingStatus] = None,
        group_id: Optional[PydanticObjectId] = None,
        discipline_id: Optional[PydanticObjectId] = None,
        teacher_id: Optional[PydanticObjectId] = None,
    ) -> list[CourseOfferingFullResponseSchema]:
        query = {}

        if status_filter is not None:
            query["status"] = status_filter

        if group_id is not None:
            query["group_id"] = group_id

        if discipline_id is not None:
            query["discipline_id"] = discipline_id

        if teacher_id is not None:
            query["teacher_id"] = teacher_id

        course_offerings = await CourseOfferingsDocument.find(query).to_list()

        return [
            await AsyncCourseOfferingsODM.to_full_course_offering_response(
                course_offering
            )
            for course_offering in course_offerings
        ]

    @staticmethod
    async def get_my_course_offerings(
        current_user: UsersDocument,
    ) -> list[CourseOfferingFullResponseSchema]:
        if current_user.permissions == Permissions.ADMIN:
            course_offerings = await CourseOfferingsDocument.find_all().to_list()

        elif current_user.permissions == Permissions.TEACHER:
            course_offerings = await CourseOfferingsDocument.find(
                CourseOfferingsDocument.teacher_id == current_user.id
            ).to_list()

        elif current_user.permissions == Permissions.STUDENT:
            if current_user.group_id is None:
                return []

            course_offerings = await CourseOfferingsDocument.find(
                CourseOfferingsDocument.group_id == current_user.group_id,
                CourseOfferingsDocument.status == CourseOfferingStatus.ACTIVE,
            ).to_list()

        else:
            course_offerings = []

        return [
            await AsyncCourseOfferingsODM.to_full_course_offering_response(
                course_offering
            )
            for course_offering in course_offerings
        ]

    @staticmethod
    async def update_course_offering(
        course_offering_id: str,
        current_user: UsersDocument,
        teacher_id: Optional[PydanticObjectId] = None,
        coursework_title: Optional[str] = None,
        coursework_desc: Optional[str] = None,
        deadline_at: Optional[datetime] = None,
        status_value: Optional[CourseOfferingStatus] = None,
    ) -> CourseOfferingsDocument:
        course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
            course_offering_id
        )

        await AsyncCourseOfferingsODM.check_course_offering_manage_permission(
            course_offering=course_offering,
            current_user=current_user,
        )

        if teacher_id is not None:
            teacher = await AsyncUsersODM.get_user_by_id(teacher_id)

            if teacher.permissions != Permissions.TEACHER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Назначенный пользователь не является преподавателем",
                )

            course_offering.teacher_id = teacher_id

        if coursework_title is not None:
            course_offering.coursework_title = coursework_title

        if coursework_desc is not None:
            course_offering.coursework_desc = coursework_desc

        if deadline_at is not None:
            course_offering.deadline_at = deadline_at

        if status_value is not None:
            course_offering.status = status_value

        course_offering.updated_at = utc_now()

        await course_offering.save()
        return course_offering

    @staticmethod
    async def close_course_offering(
        course_offering_id: str,
        current_user: UsersDocument,
    ) -> CourseOfferingsDocument:
        course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
            course_offering_id
        )

        await AsyncCourseOfferingsODM.check_course_offering_manage_permission(
            course_offering=course_offering,
            current_user=current_user,
        )

        course_offering.status = CourseOfferingStatus.CLOSED
        course_offering.updated_at = utc_now()

        await course_offering.save()
        return course_offering

    @staticmethod
    async def delete_course_offering(
        course_offering_id: str,
        current_user: UsersDocument,
    ) -> None:
        course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
            course_offering_id
        )

        await AsyncCourseOfferingsODM.check_course_offering_manage_permission(
            course_offering=course_offering,
            current_user=current_user,
        )

        await course_offering.delete()

    @staticmethod
    async def get_course_offering_analytics(
        course_offering_id: str,
        current_user: UsersDocument,
    ) -> CourseOfferingAnalyticsSchema:
        from src.submissions.documents import SubmissionStatus, SubmissionsDocument

        course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
            course_offering_id
        )

        if current_user.permissions == Permissions.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Студент не может смотреть аналитику",
            )

        if (
            current_user.permissions == Permissions.TEACHER
            and course_offering.teacher_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к аналитике этой курсовой",
            )

        students = await UsersDocument.find(
            UsersDocument.group_id == course_offering.group_id,
            UsersDocument.permissions == Permissions.STUDENT,
        ).to_list()

        submissions = await SubmissionsDocument.find(
            SubmissionsDocument.course_offering_id == course_offering.id
        ).to_list()

        latest_submissions_by_student = {}

        for submission in submissions:
            student_key = str(submission.student_id)
            current_latest = latest_submissions_by_student.get(student_key)

            if current_latest is None:
                latest_submissions_by_student[student_key] = submission
                continue

            if submission.attempt_no > current_latest.attempt_no:
                latest_submissions_by_student[student_key] = submission

        total_students = len(students)
        submitted_students_count = len(latest_submissions_by_student)
        not_submitted_students_count = total_students - submitted_students_count

        credited_count = 0
        not_credited_count = 0
        waiting_review_count = 0

        for submission in latest_submissions_by_student.values():
            if submission.status == SubmissionStatus.CREDITED:
                credited_count += 1
            elif submission.status == SubmissionStatus.NOT_CREDITED:
                not_credited_count += 1
            elif submission.status == SubmissionStatus.SUBMITTED:
                waiting_review_count += 1

        if total_students > 0:
            submission_percent = round(
                submitted_students_count / total_students * 100,
                2,
            )
            credited_percent = round(
                credited_count / total_students * 100,
                2,
            )
        else:
            submission_percent = 0
            credited_percent = 0

        not_submitted_students = [
            AnalyticsStudentSchema(
                id=student.id,
                username=student.username,
                name=student.name,
                last_name=student.last_name,
            )
            for student in students
            if str(student.id) not in latest_submissions_by_student
        ]

        discipline_name = None
        group_name = None

        try:
            discipline = await AsyncDisciplinesODM.get_discipline_by_id(
                course_offering.discipline_id
            )
            discipline_name = discipline.name
        except HTTPException:
            pass

        try:
            group = await AsyncGroupsODM.get_group_by_id(course_offering.group_id)
            group_name = group.name
        except HTTPException:
            pass

        return CourseOfferingAnalyticsSchema(
            course_offering_id=course_offering.id,
            coursework_title=course_offering.coursework_title,
            discipline_id=course_offering.discipline_id,
            discipline_name=discipline_name,
            group_id=course_offering.group_id,
            group_name=group_name,
            teacher_id=course_offering.teacher_id,
            total_students=total_students,
            submitted_students_count=submitted_students_count,
            not_submitted_students_count=not_submitted_students_count,
            credited_count=credited_count,
            not_credited_count=not_credited_count,
            waiting_review_count=waiting_review_count,
            submitted_count_total=len(submissions),
            submission_percent=submission_percent,
            credited_percent=credited_percent,
            not_submitted_students=not_submitted_students,
        )

    @staticmethod
    async def check_course_offering_manage_permission(
        course_offering: CourseOfferingsDocument,
        current_user: UsersDocument,
    ) -> None:
        if current_user.permissions == Permissions.ADMIN:
            return

        if (
            current_user.permissions == Permissions.TEACHER
            and course_offering.teacher_id == current_user.id
        ):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для управления этой курсовой",
        )

    @staticmethod
    async def check_course_offering_view_permission(
        course_offering: CourseOfferingsDocument,
        current_user: UsersDocument,
    ) -> None:
        if current_user.permissions == Permissions.ADMIN:
            return

        if (
            current_user.permissions == Permissions.TEACHER
            and course_offering.teacher_id == current_user.id
        ):
            return

        if (
            current_user.permissions == Permissions.STUDENT
            and current_user.group_id == course_offering.group_id
            and course_offering.status == CourseOfferingStatus.ACTIVE
        ):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой курсовой",
        )

    @staticmethod
    async def to_course_offering_response(
        course_offering: CourseOfferingsDocument,
    ) -> CourseOfferingResponseSchema:
        return CourseOfferingResponseSchema(
            id=course_offering.id,
            discipline_id=course_offering.discipline_id,
            group_id=course_offering.group_id,
            teacher_id=course_offering.teacher_id,
            coursework_title=course_offering.coursework_title,
            coursework_desc=course_offering.coursework_desc,
            deadline_at=course_offering.deadline_at,
            status=course_offering.status,
            created_at=course_offering.created_at,
            updated_at=course_offering.updated_at,
        )

    @staticmethod
    async def to_full_course_offering_response(
        course_offering: CourseOfferingsDocument,
    ) -> CourseOfferingFullResponseSchema:
        discipline_name = None
        group_name = None
        teacher_name = None
        teacher_last_name = None

        try:
            discipline = await AsyncDisciplinesODM.get_discipline_by_id(
                course_offering.discipline_id
            )
            discipline_name = discipline.name
        except HTTPException:
            pass

        try:
            group = await AsyncGroupsODM.get_group_by_id(course_offering.group_id)
            group_name = group.name
        except HTTPException:
            pass

        try:
            teacher = await AsyncUsersODM.get_user_by_id(course_offering.teacher_id)
            teacher_name = teacher.name
            teacher_last_name = teacher.last_name
        except HTTPException:
            pass

        return CourseOfferingFullResponseSchema(
            id=course_offering.id,
            discipline_id=course_offering.discipline_id,
            group_id=course_offering.group_id,
            teacher_id=course_offering.teacher_id,
            coursework_title=course_offering.coursework_title,
            coursework_desc=course_offering.coursework_desc,
            deadline_at=course_offering.deadline_at,
            status=course_offering.status,
            created_at=course_offering.created_at,
            updated_at=course_offering.updated_at,
            discipline_name=discipline_name,
            group_name=group_name,
            teacher_name=teacher_name,
            teacher_last_name=teacher_last_name,
        )