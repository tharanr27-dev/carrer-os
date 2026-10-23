"""Private local-disk file storage for uploads.

Files live under UPLOAD_DIR (git-ignored) and are only ever served through authenticated, ownership-checked
endpoints. This replaces the earlier simulated S3 client that never stored anything.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("careeros")


class LocalFileStorage:
    def __init__(self, base_dir: str):
        self.base = Path(base_dir).resolve()

    def _path(self, key: str) -> Path:
        p = (self.base / key).resolve()
        if self.base != p and self.base not in p.parents:  # never escape the storage root
            raise ValueError("Invalid storage key")
        return p

    async def save(self, key: str, data: bytes) -> None:
        path = self._path(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(_write)

    async def read(self, key: str) -> Optional[bytes]:
        path = self._path(key)
        return await asyncio.to_thread(lambda: path.read_bytes() if path.is_file() else None)

    async def delete(self, key: str) -> bool:
        path = self._path(key)

        def _rm() -> bool:
            if path.is_file():
                path.unlink()
                return True
            return False

        return await asyncio.to_thread(_rm)


def get_file_storage() -> LocalFileStorage:
    return LocalFileStorage(settings.UPLOAD_DIR)
