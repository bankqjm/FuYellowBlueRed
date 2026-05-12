from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.base import ResponseSchema
from app.deps.auth import get_current_user
from app.config import settings
import os
import uuid
import aiofiles

router = APIRouter(prefix="/upload", tags=["文件上传"])


@router.post("", response_model=ResponseSchema[str])
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise ValueError(f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)

    file_url = f"/uploads/{filename}"

    return ResponseSchema(
        code=0,
        message="上传成功",
        data=file_url,
    )
