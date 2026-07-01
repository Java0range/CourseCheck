from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Request

from src.course_offerings.documents import CourseOfferingStatus
from src.course_offerings.odm import AsyncCourseOfferingsODM
from src.course_offerings.schemas import (
    CreateCourseOfferingSchema,
    UpdateCourseOfferingSchema,
)
from src.users.documents import Permissions
from src.users.utils import get_current_user, permission_required


router = APIRouter(prefix="/course-offerings", tags=["Course Offerings"])


@router.post("")
@permission_required(Permissions.ADMIN)
async def create_course_offering(
    request: Request,
    json: CreateCourseOfferingSchema,
):
    course_offering = await AsyncCourseOfferingsODM.create_course_offering(
        discipline_id=json.discipline_id,
        group_id=json.group_id,
        teacher_id=json.teacher_id,
        coursework_title=json.coursework_title,
        coursework_desc=json.coursework_desc,
        deadline_at=json.deadline_at,
    )

    return await AsyncCourseOfferingsODM.to_full_course_offering_response(
        course_offering
    )


@router.get("")
@permission_required(Permissions.ADMIN)
async def get_course_offerings(
    request: Request,
    status_filter: Optional[CourseOfferingStatus] = None,
    group_id: Optional[PydanticObjectId] = None,
    discipline_id: Optional[PydanticObjectId] = None,
    teacher_id: Optional[PydanticObjectId] = None,
):
    return await AsyncCourseOfferingsODM.get_all_course_offerings(
        status_filter=status_filter,
        group_id=group_id,
        discipline_id=discipline_id,
        teacher_id=teacher_id,
    )


@router.get("/my")
@permission_required(Permissions.STUDENT)
async def get_my_course_offerings(request: Request):
    current_user = await get_current_user(request)

    return await AsyncCourseOfferingsODM.get_my_course_offerings(
        current_user=current_user
    )


@router.get("/{course_offering_id}/analytics")
@permission_required(Permissions.TEACHER)
async def get_course_offering_analytics(
    request: Request,
    course_offering_id: str,
):
    current_user = await get_current_user(request)

    return await AsyncCourseOfferingsODM.get_course_offering_analytics(
        course_offering_id=course_offering_id,
        current_user=current_user,
    )


@router.get("/{course_offering_id}")
@permission_required(Permissions.STUDENT)
async def get_course_offering(request: Request, course_offering_id: str):
    current_user = await get_current_user(request)

    course_offering = await AsyncCourseOfferingsODM.get_course_offering_by_id(
        course_offering_id
    )

    await AsyncCourseOfferingsODM.check_course_offering_view_permission(
        course_offering=course_offering,
        current_user=current_user,
    )

    return await AsyncCourseOfferingsODM.to_full_course_offering_response(
        course_offering
    )


@router.put("/{course_offering_id}")
@permission_required(Permissions.TEACHER)
async def update_course_offering(
    request: Request,
    course_offering_id: str,
    json: UpdateCourseOfferingSchema,
):
    current_user = await get_current_user(request)

    course_offering = await AsyncCourseOfferingsODM.update_course_offering(
        course_offering_id=course_offering_id,
        current_user=current_user,
        teacher_id=json.teacher_id,
        coursework_title=json.coursework_title,
        coursework_desc=json.coursework_desc,
        deadline_at=json.deadline_at,
        status_value=json.status,
    )

    return await AsyncCourseOfferingsODM.to_full_course_offering_response(
        course_offering
    )


@router.post("/{course_offering_id}/close")
@permission_required(Permissions.TEACHER)
async def close_course_offering(request: Request, course_offering_id: str):
    current_user = await get_current_user(request)

    course_offering = await AsyncCourseOfferingsODM.close_course_offering(
        course_offering_id=course_offering_id,
        current_user=current_user,
    )

    return await AsyncCourseOfferingsODM.to_full_course_offering_response(
        course_offering
    )


@router.delete("/{course_offering_id}")
@permission_required(Permissions.TEACHER)
async def delete_course_offering(request: Request, course_offering_id: str):
    current_user = await get_current_user(request)

    await AsyncCourseOfferingsODM.delete_course_offering(
        course_offering_id=course_offering_id,
        current_user=current_user,
    )

    return {"detail": "Курсовая удалена"}