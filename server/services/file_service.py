"""
File Service
Handles file storage operations with security checks
"""

import logging
import re
import uuid
from pathlib import Path
from typing import Optional

from ..config import get_storage_path

logger = logging.getLogger(__name__)

# Valid storage categories
VALID_CATEGORIES = ["contracts", "kb_documents", "reports"]

# Safe file extensions
SAFE_EXTENSIONS = {
    "pdf", "doc", "docx", "txt", "md",
    "jpg", "jpeg", "png", "gif",
}


class FileService:
    """File storage service with security enhancements"""

    def __init__(self):
        self.storage_root = get_storage_path()

    def ensure_storage_dirs(self):
        """Ensure all storage directories exist"""
        (self.storage_root / "contracts").mkdir(parents=True, exist_ok=True)
        (self.storage_root / "kb_documents").mkdir(parents=True, exist_ok=True)
        (self.storage_root / "reports").mkdir(parents=True, exist_ok=True)

    def _validate_category(self, category: str) -> None:
        """Validate storage category"""
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category: {category}. Must be one of {VALID_CATEGORIES}"
            )

    def _extract_safe_extension(self, filename: str) -> str:
        """
        Extract safe extension from filename

        Args:
            filename: Original filename

        Returns:
            Extension with dot (e.g., ".pdf") or empty string
        """
        ext_match = re.search(r"\.([a-zA-Z0-9]+)$", filename)
        if ext_match:
            ext = ext_match.group(1).lower()
            if ext in SAFE_EXTENSIONS:
                return f".{ext}"
            logger.warning(f"File extension '{ext}' not in safe list, using no extension")
        return ""

    def _validate_path_security(self, full_path: Path) -> None:
        """
        Validate that path is within storage_root (prevent path traversal)

        Args:
            full_path: Resolved absolute path to validate

        Raises:
            ValueError: If path traversal detected
        """
        try:
            full_path.resolve().relative_to(self.storage_root.resolve())
        except ValueError:
            raise ValueError("Path traversal detected: attempted access outside storage root")

    def save_file(
        self,
        category: str,
        filename: str,
        content: bytes,
        use_uuid: bool = True,
    ) -> str:
        """
        Securely save a file to storage with UUID naming

        Args:
            category: Storage category (contracts, kb_documents, reports)
            filename: Original filename (only used for extension extraction)
            content: File content
            use_uuid: Whether to use UUID for filename (default True, highly recommended)

        Returns:
            Object key (relative path)

        Raises:
            ValueError: If category invalid or path traversal detected
        """
        # Validate category
        self._validate_category(category)

        category_path = self.storage_root / category
        category_path.mkdir(parents=True, exist_ok=True)

        # Extract safe extension
        ext = self._extract_safe_extension(filename)

        # Use UUID subdirectory + filename to prevent path traversal
        uuid_dir = uuid.uuid4().hex[:8]
        if use_uuid:
            safe_filename = f"{uuid.uuid4().hex[:16]}{ext}"
        else:
            # Still use UUID for safety
            safe_filename = f"{uuid.uuid4().hex}{ext}"

        object_key = f"{category}/{uuid_dir}/{safe_filename}"
        full_path = self.storage_root / object_key
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Security check: ensure path is within storage_root
        self._validate_path_security(full_path)

        with open(full_path, "wb") as f:
            f.write(content)

        logger.debug(f"File saved: {object_key}")
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
        Securely delete a file with path traversal checks

        Args:
            object_key: Object key

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If path traversal detected
        """
        # Prevent path traversal
        if ".." in object_key or object_key.startswith("/"):
            raise ValueError("Invalid object key: potential path traversal")

        file_path = self.get_file_path(object_key)

        # Security check
        try:
            file_path_resolved = Path(file_path).resolve()
            file_path_resolved.relative_to(self.storage_root.resolve())
        except ValueError:
            raise ValueError("Path traversal detected")

        if not file_path_resolved.exists():
            return False

        file_path_resolved.unlink()
        logger.debug(f"File deleted: {object_key}")
        return True

    def file_exists(self, object_key: str) -> bool:
        """Check if file exists"""
        # Prevent path traversal in existence checks
        if ".." in object_key or object_key.startswith("/"):
            return False
        return Path(self.get_file_path(object_key)).exists()
