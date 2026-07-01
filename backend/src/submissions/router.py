from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile

from src.submissions.documents import SubmissionStatus
from src.submissions.odm import AsyncSubmissionsODM
from src.submissions.schemas import ReviewSubmissionSchema
from src.users.documents import Permissions
from src.users.utils import get_current_user, permission_required, role_required


router = APIRouter(tags=["Submissions"])


@router.post("/course-offerings/{course_offering_id}/submit")
@role_required(Permissions.STUDENT)
async def submit_coursework(
    request: Request,
    course_offering_id: str,
    file: UploadFile = File(...),
    student_comment: Optional[str] = Form(default=None),
):
    current_user = await get_current_user(request)

    submission = await AsyncSubmissionsODM.create_submission(
        course_offering_id=course_offering_id,
        current_user=current_user,
        file=file,
        student_comment=student_comment,
    )

    return await AsyncSubmissionsODM.to_full_submission_response(submission)


@router.get("/submissions/my")
@role_required(Permissions.STUDENT)
async def get_my_submissions(request: Request):
    current_user = await get_current_user(request)

    return await AsyncSubmissionsODM.get_my_submissions(
        current_user=current_user,
    )


@router.get("/course-offerings/{course_offering_id}/my-submissions")
@role_required(Permissions.STUDENT)
async def get_my_coursework_submissions(
    request: Request,
    course_offering_id: str,
):
    current_user = await get_current_user(request)

    return await AsyncSubmissionsODM.get_student_course_offering_submissions(
        course_offering_id=course_offering_id,
        current_user=current_user,
    )


@router.get("/course-offerings/{course_offering_id}/submissions")
@permission_required(Permissions.TEACHER)
async def get_course_offering_submissions(
    request: Request,
    course_offering_id: str,
    status_filter: Optional[SubmissionStatus] = None,
):
    current_user = await get_current_user(request)

    return await AsyncSubmissionsODM.get_course_offering_submissions(
        course_offering_id=course_offering_id,
        current_user=current_user,
        status_filter=status_filter,
    )


@router.get("/submissions/{submission_id}")
@permission_required(Permissions.STUDENT)
async def get_submission(request: Request, submission_id: str):
    current_user = await get_current_user(request)

    submission = await AsyncSubmissionsODM.get_submission_by_id(submission_id)

    await AsyncSubmissionsODM.check_submission_view_permission(
        submission=submission,
        current_user=current_user,
    )

    return await AsyncSubmissionsODM.to_full_submission_response(submission)


@router.patch("/submissions/{submission_id}/review")
@permission_required(Permissions.TEACHER)
async def review_submission(
    request: Request,
    submission_id: str,
    json: ReviewSubmissionSchema,
):
    current_user = await get_current_user(request)

    submission = await AsyncSubmissionsODM.review_submission(
        submission_id=submission_id,
        current_user=current_user,
        status_value=json.status,
        teacher_comment=json.teacher_comment,
    )

    return await AsyncSubmissionsODM.to_full_submission_response(submission)