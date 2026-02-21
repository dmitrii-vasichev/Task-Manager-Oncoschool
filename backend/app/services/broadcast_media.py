import uuid
from pathlib import Path, PurePosixPath

from aiogram.types import FSInputFile

from app.services.supabase_storage import SupabaseStorageService

ALLOWED_BROADCAST_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_BROADCAST_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB

_STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
_BROADCAST_MEDIA_DIR = _STATIC_DIR / "broadcasts"


def _sanitize_media_path(value: str) -> str:
    normalized = PurePosixPath(value.strip())
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError("Invalid media path")
    return normalized.as_posix().lstrip("/")


def validate_broadcast_image_payload(
    content_type: str | None,
    payload: bytes,
) -> tuple[str, str]:
    normalized_content_type = (content_type or "").lower().strip()
    extension = ALLOWED_BROADCAST_IMAGE_TYPES.get(normalized_content_type)
    if not extension:
        raise ValueError("Допустимые форматы: JPEG, PNG, WebP")
    if not payload:
        raise ValueError("Прикреплённый файл пустой")
    if len(payload) > MAX_BROADCAST_IMAGE_BYTES:
        raise ValueError("Картинка слишком большая (максимум 10 МБ)")
    return normalized_content_type, extension


async def save_broadcast_image(
    *,
    payload: bytes,
    content_type: str,
    storage_service: SupabaseStorageService | None,
) -> str:
    _, extension = validate_broadcast_image_payload(content_type, payload)
    media_path = f"broadcasts/{uuid.uuid4().hex}.{extension}"

    if storage_service:
        await storage_service.upload(media_path, payload, content_type=content_type)
        return media_path

    local_path = _STATIC_DIR / _sanitize_media_path(media_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(payload)
    return media_path


def get_broadcast_photo(
    *,
    media_path: str,
    storage_service: SupabaseStorageService | None,
):
    safe_path = _sanitize_media_path(media_path)

    if storage_service:
        return storage_service.get_public_url(safe_path)

    local_path = _STATIC_DIR / safe_path
    if not local_path.exists():
        raise FileNotFoundError(str(local_path))
    return FSInputFile(str(local_path))


async def delete_broadcast_image(
    *,
    media_path: str,
    storage_service: SupabaseStorageService | None,
) -> None:
    safe_path = _sanitize_media_path(media_path)

    if storage_service:
        await storage_service.delete([safe_path])
        return

    local_path = _STATIC_DIR / safe_path
    if local_path.exists():
        local_path.unlink()

    # Best effort cleanup for empty leaf directory.
    if local_path.parent != _BROADCAST_MEDIA_DIR and local_path.parent.exists():
        try:
            local_path.parent.rmdir()
        except OSError:
            pass
