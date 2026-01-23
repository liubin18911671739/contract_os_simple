"""
Parse Agent - Extract text from contract files
"""

from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import ContractVersion, PrecheckTask
from server.services.contract_service import ContractService
from server.utils.file_parser import parse_file
from server.agents.base import BaseAgent


class ParseAgent(BaseAgent):
    """Extract text from contract files (PDF, DOCX, TXT)"""

    stage_name = "PARSING"

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.contract_service = ContractService(session)

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse contract file and extract text

        Args:
            task_id: Task ID
            payload: Empty dict (first stage)

        Returns:
            Dict with parsed text and metadata
        """
        # Get task
        task = await self.session.get(PrecheckTask, task_id)
        if not task:
            raise ValueError("Task not found")

        # Get contract version
        contract_version = await self.session.get(
            ContractVersion, task.contract_version_id
        )
        if not contract_version:
            raise ValueError("Contract version not found")

        mime_type = contract_version.mime
        sha256 = contract_version.sha256

        # Get file content
        file_content = await self.contract_service.get_contract_version_content(
            task.contract_version_id
        )

        if not file_content:
            raise ValueError("File content not found")

        # Parse file
        try:
            text = parse_file(file_content, mime_type)
        except ValueError as e:
            raise ValueError(f"Failed to parse file: {str(e)}")

        # Validate text
        if not text or text.strip() == "":
            raise ValueError("Parsed text is empty")

        await self.update_progress(task_id, 12)

        return {
            "text": text,
            "mime_type": mime_type,
            "metadata": {
                "sha256": sha256,
                "file_size": len(file_content),
            },
        }
