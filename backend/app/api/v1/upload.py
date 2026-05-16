from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.base import ResponseSchema
from app.deps.auth import get_current_user
from app.config import settings
from app.core import BadRequestException, get_logger
import os
import uuid
import aiofiles

router = APIRouter(prefix="/upload", tags=["文件上传"])
logger = get_logger("upload")

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'}
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("", response_model=ResponseSchema[str])
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise BadRequestException(f"文件大小不能超过 {MAX_FILE_SIZE // 1024 // 1024}MB")

    if len(content) == 0:
        raise BadRequestException("文件不能为空")

    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestException(f"不支持的文件类型，仅允许: {', '.join(ALLOWED_EXTENSIONS)}")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise BadRequestException(f"文件类型不匹配，实际类型: {file.content_type}")

    image_signatures = {
        b'\xff\xd8\xff': 'jpeg',
        b'\x89PNG': 'png',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'RIFF': 'webp',
    }

    file_start = content[:12]
    detected_type = None
    for sig, file_type in image_signatures.items():
        if file_start.startswith(sig):
            detected_type = file_type
            break

    if detected_type is None and ext in ['.jpg', '.jpeg']:
        if not file_start[:3] == b'\xff\xd8\xff':
            raise BadRequestException("文件内容不是有效的JPEG图像")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    file_url = f"/uploads/{filename}"
    logger.info(f"File uploaded: {filename}, user={current_user.id}, size={len(content)}")

    return ResponseSchema(
        code=0,
        message="上传成功",
        data=file_url,
    )
