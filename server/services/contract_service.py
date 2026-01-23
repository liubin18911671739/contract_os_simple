"""
Contract Service
Manages contracts and versions
"""

import hashlib
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_storage_path
from ..database.models import Contract, ContractVersion
from .file_service import FileService


class ContractService:
    """Contract management service"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.file_service = FileService()

    async def create_contract(
        self,
        contract_name: str,
        counterparty: Optional[str] = None,
        contract_type: Optional[str] = None,
    ) -> str:
        """
        Create a new contract

        Args:
            contract_name: Contract name
            counterparty: Counterparty name
            contract_type: Contract type

        Returns:
            Contract ID
        """
        contract_id = f"contract_{uuid.uuid4().hex[:12]}"

        contract = Contract(
            id=contract_id,
            contract_name=contract_name,
            counterparty=counterparty,
            contract_type=contract_type,
        )

        self.session.add(contract)
        await self.session.commit()

        return contract_id

    async def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contract with versions

        Args:
            contract_id: Contract ID

        Returns:
            Contract dict or None
        """
        contract = await self.session.get(Contract, contract_id)

        if not contract:
            return None

        # Get versions
        query = (
            select(ContractVersion)
            .where(ContractVersion.contract_id == contract_id)
            .order_by(ContractVersion.version_no.desc())
        )

        result = await self.session.execute(query)
        versions = result.scalars().all()

        return {
            "id": contract.id,
            "contract_name": contract.contract_name,
            "counterparty": contract.counterparty,
            "contract_type": contract.contract_type,
            "created_at": contract.created_at.isoformat(),
            "versions": [
                {
                    "id": v.id,
                    "version_no": v.version_no,
                    "mime": v.mime,
                    "sha256": v.sha256,
                    "created_at": v.created_at.isoformat(),
                }
                for v in versions
            ],
        }

    async def upload_contract_version(
        self,
        contract_id: str,
        file_content: bytes,
        filename: str,
        mime_type: str,
    ) -> Dict[str, Any]:
        """
        Upload a new contract version

        Args:
            contract_id: Contract ID
            file_content: File bytes
            filename: Original filename
            mime_type: MIME type

        Returns:
            Version info
        """
        # Calculate hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Get next version number
        query = (
            select(ContractVersion)
            .where(ContractVersion.contract_id == contract_id)
            .order_by(ContractVersion.version_no.desc())
        )

        result = await self.session.execute(query)
        last_version = result.first()

        next_version = (last_version[0].version_no + 1) if last_version else 1

        # Store file
        storage_path = get_storage_path("contracts")
        storage_path.mkdir(parents=True, exist_ok=True)

        object_key = f"{contract_id}/v{next_version}_{filename}"
        full_path = storage_path / object_key

        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_content)

        # Create version record
        version_id = f"version_{uuid.uuid4().hex[:12]}"
        version = ContractVersion(
            id=version_id,
            contract_id=contract_id,
            version_no=next_version,
            object_key=object_key,
            sha256=file_hash,
            mime=mime_type,
        )

        self.session.add(version)
        await self.session.commit()

        return {
            "id": version_id,
            "version_no": next_version,
            "object_key": object_key,
            "sha256": file_hash,
        }

    async def get_contract_version_path(self, version_id: str) -> Optional[str]:
        """
        Get file path for a contract version

        Args:
            version_id: Version ID

        Returns:
            File path or None
        """
        version = await self.session.get(ContractVersion, version_id)

        if not version:
            return None

        storage_path = get_storage_path("contracts")
        return str(storage_path / version.object_key)

    async def get_contract_version_content(self, version_id: str) -> Optional[bytes]:
        """
        Get file content for a contract version

        Args:
            version_id: Version ID

        Returns:
            File content or None
        """
        file_path = await self.get_contract_version_path(version_id)

        if not file_path:
            return None

        with open(file_path, "rb") as f:
            return f.read()
