
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace
import json

import filetype

from fastapi import UploadFile, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from redis.asyncio import Redis

from app.models.students_model import Student
from app.models.files_model import UploadedFiles, ProfilePicture
from app.repository import file_repository as repo
from app.storage.s3storage import storage


FILES_PREFIX = "files"
PROFILE_PREFIX = "profile_pictures"

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/jpg",
    "image/webp",
}

ALLOWED_DOCUMENT_TYPES = ALLOWED_IMAGE_TYPES | {"application/pdf"}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

CACHE_TTL = 300  # 5 minutes


def _detect_and_validate(content: bytes, allowed_types: set) -> str:
    kind = filetype.guess(content)

    if kind is None:
        raise HTTPException(status_code=400, detail="Invalid file.")
    if kind.mime not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed.")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size should not exceed 5 MB.")

    return kind.mime


def _file_cache_key(student_id: int, file_id: int) -> str:
    return f"file:{student_id}:{file_id}"


async def upload_user_profile_picture(profile: UploadFile,db: AsyncSession,current_user: Student):
    content = await profile.read()

    mime = _detect_and_validate(content,ALLOWED_IMAGE_TYPES)
    existing = await repo.get_profile_picture(db,current_user.id)
    extension = Path(profile.filename or "").suffix
    stored_name = f"{uuid4()}{extension}"

    storage_key = (f"{PROFILE_PREFIX}/{current_user.id}/{stored_name}")

    await run_in_threadpool(storage.upload,storage_key,content, mime)

    try:
        picture = ProfilePicture(
            student_id=current_user.id,
            filename=profile.filename or stored_name,
            content_type=mime,
            file_path=storage_key,
            stored_name=stored_name,
        )

        result = await repo.upload_profile_picture(db, picture)

        if existing:
            try:
                await run_in_threadpool(storage.delete,existing.file_path)
            except Exception:
                pass
        return result

    except Exception:
        await run_in_threadpool(
            storage.delete,
            storage_key
        )
        raise


async def delete_user_profile_picture(db: AsyncSession, current_user: Student):
    existing = await repo.get_profile_picture(db, current_user.id)

    if existing is None:
        raise HTTPException( status_code=404,detail="No profile picture found")
    await run_in_threadpool(storage.delete,existing.file_path)

    return await repo.delete_profile_picture(db,current_user.id)


async def view_profile_picture_content(db: AsyncSession,current_user: Student):
    picture = await repo.get_profile_picture(db, current_user.id)

    if picture is None:
        raise HTTPException(status_code=404,detail="No profile picture set")

    content = await run_in_threadpool(storage.download,picture.file_path)
    return Response(content=content,media_type=picture.content_type)



async def upload_user_file( profile: UploadFile,category: str,db: AsyncSession, current_user: Student):
    content = await profile.read()
    mime = _detect_and_validate(content,ALLOWED_DOCUMENT_TYPES)

    count = await repo.count_files_by_category(db,current_user.id,category)

    if category.lower() == "photo" and count >= 10:
        raise HTTPException( status_code=400,detail="Maximum 10 photos allowed.")

    if category.lower() == "document" and count >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 documents allowed.")

    extension = Path(profile.filename or "").suffix
    stored_name = f"{uuid4()}{extension}"

    storage_key = (f"{FILES_PREFIX}/{current_user.id}/{stored_name}")

    await run_in_threadpool(storage.upload,storage_key,content,mime)

    new_file = UploadedFiles(
        student_id=current_user.id,
        name=profile.filename,
        filename=profile.filename,
        stored_name=stored_name,
        file_path=storage_key,
        content_type=mime,
        category=category,
    )

    try:
        return await repo.upload_files( db, new_file)

    except Exception:
        await run_in_threadpool( storage.delete,storage_key)
        raise


#
async def get_file(
    file_id: int,
    db: AsyncSession,
    current_user: Student,
    redis: Redis
):
    cache_key = _file_cache_key(
        current_user.id,
        file_id
    )

  
    cache_file = await redis.get(cache_key)
    if cache_file:
        cached_data = json.loads(cache_file)

        # Convert dictionary into an object that supports
        # attribute access, such as file.file_path.
        return SimpleNamespace(**cached_data)

    # 2. Cache miss: fetch from PostgreSQL
    file = await repo.view_file(
        db,
        file_id
    )

    if file is None:
        raise HTTPException(status_code=404,detail="File not found")

    # 3. Check ownership
    if file.student_id != current_user.id:
        raise HTTPException( status_code=403,detail="Not authorized to access this file")

  
    exists = await run_in_threadpool(storage.exists,file.file_path)

    if not exists:
        raise HTTPException(status_code=404,detail="File missing from storage")

   
    file_data = {
        "id": file.id,
        "student_id": file.student_id,
        "name": file.name,
        "filename": file.filename,
        "stored_name": file.stored_name,
        "file_path": file.file_path,
        "content_type": file.content_type,
        "category": file.category,
    }

    # 6. Store metadata in Redis for 5 minutes
    await redis.set(
        cache_key,
        json.dumps(file_data),
        ex=CACHE_TTL
    )

    return file


async def view_file_content(
    file_id: int,
    db: AsyncSession,
    current_user: Student,
    redis: Redis
):
    file = await get_file(
        file_id,
        db,
        current_user,
        redis
    )

    content = await run_in_threadpool(
        storage.download,
        file.file_path
    )

    return Response(
        content=content,
        media_type=file.content_type
    )


async def remove_file(
    file_id: int,
    db: AsyncSession,
    current_user: Student,
    redis: Redis
):
    file = await get_file(
        file_id,
        db,
        current_user,
        redis
    )

    await run_in_threadpool(
        storage.delete,
        file.file_path
    )

    result = await repo.delete_files(
        db,
        file_id
    )

    # Invalidate cached metadata after deletion
    cache_key = _file_cache_key(
        current_user.id,
        file_id
    )

    await redis.delete(cache_key)

    return result


async def download_file_content(
    file_id: int,
    db: AsyncSession,
    current_user: Student,
    redis: Redis
):
    file = await get_file(
        file_id,
        db,
        current_user,
        redis
    )

    content = await run_in_threadpool(
        storage.download,
        file.file_path
    )

    return Response(
        content=content,
        media_type=file.content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{file.filename}"'
            )
        }
    )


async def get_all_user_files(
    db: AsyncSession,
    current_user: Student
):
    return await repo.get_all_files_by_student(
        db,
        current_user.id
    )
