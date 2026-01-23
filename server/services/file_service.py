"""
File Service
Handles file storage operations
"""

import os
from pathlib import Path
from typing import Optional

from ..config import get_storage_path


class FileService:
    """File storage service"""

    def __init__(self):
        self.storage_root = get_storage_path()

    def ensure_storage_dirs(self):
        """Ensure all storage directories exist"""
        (self.storage_root / "contracts").mkdir(parents=True, exist_ok=True)
        (self.storage_root / "kb_documents").mkdir(parents=True, exist_ok=True)
        (self.storage_root / "reports").mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        category: str,
        filename: str,
        content: bytes,
    ) -> str:
        """
        Save a file to storage

        Args:
            category: Storage category (contracts, kb_documents, reports)
            filename: Filename
            content: File content

        Returns:
            Object key (relative path)
        """
        category_path = self.storage_root / category
        category_path.mkdir(parents=True, exist_ok=True)

        object_key = f"{category}/{filename}"
        full_path = self.storage_root / object_key

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(content)

        return object_key

    def get_file_path(self, object_key: str) -> str:
        """
        Get full path for an object key

        Args:
            object_key: Object key

        Returns:
            Full file path
        """
        return str(self.storage_root / object_key)

    def get_file_content(self, object_key: str) -> Optional[bytes]:
        """
        Get file content

        Args:
            object_key: Object key

        Returns:
            File content or None
        """
        file_path = self.get_file_path(object_key)

        if not Path(file_path).exists():
            return None

        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file

        Args:
            object_key: Object key

        Returns:
            True if deleted, False if not found
        """
        file_path = self.get_file_path(object_key)

        if not Path(file_path).exists():
            return False

        Path(file_path).unlink()
        return True

    def file_exists(self, object_key: str) -> bool:
        """Check if file exists"""
        return Path(self.get_file_path(object_key)).exists()
