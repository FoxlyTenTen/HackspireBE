import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings


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


def get_storage() -> StorageBackend:
    return LocalDiskStorage(settings.upload_dir)
