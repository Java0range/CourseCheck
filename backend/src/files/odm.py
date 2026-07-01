import os
import shutil
from pathlib import Path
from uuid import uuid4

from beanie import PydanticObjectId
from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from src.files.documents import FilesDocument
from src.files.schemas import FileResponseSchema
from src.users.documents import Permissions, UsersDocument
from src.users.odm import parse_object_id


UPLOAD_DIR = Path("uploads/courseworks")


class AsyncFilesODM:
    @staticmethod
    async def save_upload_file(
        file: UploadFile,
        owner_id: PydanticObjectId,
    ) -> FilesDocument:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл не передан",
            )

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        original_name = file.filename
        extension = Path(original_name).suffix
        stored_name = f"{uuid4().hex}{extension}"
        path = UPLOAD_DIR / stored_name

        size = 0

        with path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                buffer.write(chunk)

        file_document = FilesDocument(
            owner_id=owner_id,
            original_name=original_name,
            stored_name=stored_name,
            path=str(path),
            content_type=file.content_type,
            size=size,
        )

        await file_document.insert()
        await file.close()

        return file_document

    @staticmethod
    async def get_file_by_id(file_id: str | PydanticObjectId) -> FilesDocument:
        if not isinstance(file_id, PydanticObjectId):
            file_id = parse_object_id(str(file_id), "Неверный id файла")

        file_document = await FilesDocument.find_one(FilesDocument.id == file_id)

        if not file_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл не найден",
            )

        return file_document

    @staticmethod
    async def check_file_access(
        file_document: FilesDocument,
        current_user: UsersDocument,
    ) -> None:
        if current_user.permissions == Permissions.ADMIN:
            return

        if (
            current_user.permissions == Permissions.STUDENT
            and file_document.owner_id == current_user.id
        ):
            return

        if current_user.permissions == Permissions.TEACHER:
            from src.submissions.documents import SubmissionsDocument

            submission = await SubmissionsDocument.find_one(
                SubmissionsDocument.file_id == file_document.id,
                SubmissionsDocument.teacher_id == current_user.id,
            )

            if submission:
                return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому файлу",
        )

    @staticmethod
    async def download_file(
        file_id: str,
        current_user: UsersDocument,
    ) -> FileResponse:
        file_document = await AsyncFilesODM.get_file_by_id(file_id)

        await AsyncFilesODM.check_file_access(
            file_document=file_document,
            current_user=current_user,
        )

        if not os.path.exists(file_document.path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл отсутствует на сервере",
            )

        return FileResponse(
            path=file_document.path,
            filename=file_document.original_name,
            media_type=file_document.content_type or "application/octet-stream",
        )

    @staticmethod
    async def delete_file(file_id: str | PydanticObjectId) -> None:
        file_document = await AsyncFilesODM.get_file_by_id(file_id)

        if os.path.exists(file_document.path):
            os.remove(file_document.path)

        await file_document.delete()

    @staticmethod
    async def to_file_response(file_document: FilesDocument) -> FileResponseSchema:
        return FileResponseSchema(
            id=file_document.id,
            owner_id=file_document.owner_id,
            original_name=file_document.original_name,
            stored_name=file_document.stored_name,
            path=file_document.path,
            content_type=file_document.content_type,
            size=file_document.size,
            uploaded_at=file_document.uploaded_at,
        )