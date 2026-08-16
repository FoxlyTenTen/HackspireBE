import mimetypes
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings
from app.services import supabase_storage


class StorageBackend(ABC):
    """File storage interface — swap LocalDiskStorage for Supabase Storage later."""

    @abstractmethod
    async def save(self, file_name: str, content: bytes) -> str:
        """Store the file and return its public URL/path."""

    @abstractmethod
    async def delete(self, file_url: str) -> None:
        """Remove the stored file; missing files are ignored."""


class LocalDiskStorage(StorageBackend):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    async def save(self, file_name: str, content: bytes) -> str:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file_name).name  # strip any client-supplied directories
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        path = self.base_dir / stored_name
        path.write_bytes(content)
        return f"/uploads/{stored_name}"

    async def delete(self, file_url: str) -> None:
        name = Path(file_url).name
        path = self.base_dir / name
        if path.is_file() and path.resolve().parent == self.base_dir.resolve():
            path.unlink()


class SupabaseStorage(StorageBackend):
    def __init__(self, bucket: str):
        self.bucket = bucket

    async def save(self, file_name: str, content: bytes) -> str:
        safe_name = Path(file_name).name  # strip any client-supplied directories
        object_path = f"{uuid.uuid4().hex}_{safe_name}"
        content_type = mimetypes.guess_type(safe_name)[0]
        return await supabase_storage.upload_object(self.bucket, object_path, content, content_type)

    async def delete(self, file_url: str) -> None:
        object_path = file_url.rsplit(f"/{self.bucket}/", 1)[-1]
        await supabase_storage.delete_object(self.bucket, object_path)


def get_materials_storage() -> StorageBackend:
    return SupabaseStorage(settings.supabase_storage_bucket_materials)


def get_announcements_storage() -> StorageBackend:
    return SupabaseStorage(settings.supabase_storage_bucket_announcements)
