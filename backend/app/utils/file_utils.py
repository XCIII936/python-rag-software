"""File upload utilities."""

import os
import uuid
import hashlib
from fastapi import UploadFile, HTTPException

from app.core.config import settings


def get_file_extension(filename: str) -> str:
    """Get the lowercase file extension."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def validate_file_upload(file: UploadFile):
    """Validate file type and size."""
    ext = get_file_extension(file.filename)
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}。支持: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )


def save_upload_file(file: UploadFile, sub_dir: str = "") -> tuple[str, str, int]:
    """Save an uploaded file and return (file_path, file_name, file_size)."""
    ext = get_file_extension(file.filename)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = os.path.join(settings.UPLOAD_DIR, sub_dir)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_name)

    content = file.file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大，最大允许 {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    file_hash = hashlib.sha256(content).hexdigest()
    return file_path, unique_name, len(content), file_hash


def delete_file(file_path: str):
    """Delete a file from disk if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)
