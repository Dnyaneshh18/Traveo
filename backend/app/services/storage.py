"""File storage — local disk (served under /uploads).  Swap for S3/Supabase Storage in production."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import ValidationFailed

settings = get_settings()

_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "application/pdf": "pdf"}


async def save_upload(file: UploadFile, *, subdir: str, owner_id: str) -> str:
    ext = _EXT.get(file.content_type or "", "bin")
    folder = Path(settings.UPLOAD_DIR) / subdir
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{owner_id}-{secrets.token_hex(6)}.{ext}"
    path = folder / name
    size = 0
    limit = settings.MAX_UPLOAD_MB * 1024 * 1024
    with path.open("wb") as fh:
        while chunk := await file.read(1024 * 256):
            size += len(chunk)
            if size > limit:
                fh.close()
                path.unlink(missing_ok=True)
                raise ValidationFailed(f"File too large (max {settings.MAX_UPLOAD_MB} MB)")
            fh.write(chunk)
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/uploads/{subdir}/{name}"
