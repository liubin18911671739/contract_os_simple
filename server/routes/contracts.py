"""
Contract routes
"""

from fastapi import (APIRouter, Depends, File, HTTPException, Request,
                     UploadFile)
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_session
from ..rate_limit import RATE_LIMITS, limiter
from ..schemas.pydantic_models import (ContractResponse, CreateContractRequest,
                                       ErrorResponse)
from ..services.contract_service import ContractService

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.post("", status_code=201)
async def create_contract(
    data: CreateContractRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new contract"""
    contract_service = ContractService(session)

    contract_id = await contract_service.create_contract(
        contract_name=data.contract_name,
        counterparty=data.counterparty,
        contract_type=data.contract_type,
    )

    return {"id": contract_id}


@router.get("/{contract_id}")
async def get_contract(
    contract_id: str,
    session: AsyncSession = Depends(get_session),
) -> ContractResponse:
    """Get contract with versions"""
    contract_service = ContractService(session)

    contract = await contract_service.get_contract(contract_id)

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return contract


@router.post("/{contract_id}/versions")
@limiter.limit(RATE_LIMITS["upload_file"])
async def upload_contract_version(
    request: Request,
    contract_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Upload a new contract version"""
    contract_service = ContractService(session)

    file_content = await file.read()

    result = await contract_service.upload_contract_version(
        contract_id=contract_id,
        file_content=file_content,
        filename=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
    )

    return result
