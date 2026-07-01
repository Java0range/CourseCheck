from fastapi import APIRouter, Request

from src.files.odm import AsyncFilesODM
from src.users.documents import Permissions
from src.users.utils import get_current_user, permission_required


router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{file_id}/download")
@permission_required(Permissions.STUDENT)
async def download_file(request: Request, file_id: str):
    current_user = await get_current_user(request)

    return await AsyncFilesODM.download_file(
        file_id=file_id,
        current_user=current_user,
    )