"""
Knowledge Base routes
"""

from fastapi import (APIRouter, Depends, File, HTTPException, Request,
                     UploadFile)
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_session
from ..rate_limit import RATE_LIMITS, limiter
from ..schemas.pydantic_models import (CreateKBCollectionRequest,
                                       KBCollectionResponse, SuccessResponse)
from ..services.kb_service import KBService

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])


@router.post("/collections", status_code=201)
@limiter.limit(RATE_LIMITS["kb_mutations"])
async def create_collection(
    request: Request,
    data: CreateKBCollectionRequest,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Create a new KB collection"""
    kb_service = KBService(session)

    collection_id = await kb_service.create_collection(
        name=data.name,
        scope=data.scope,
    )

    return SuccessResponse(success=True, id=collection_id)


@router.get("/collections")
async def list_collections(
    scope: str = None,
    is_enabled: bool = None,
    session: AsyncSession = Depends(get_session),
) -> list[KBCollectionResponse]:
    """List KB collections"""
    kb_service = KBService(session)

    collections = await kb_service.list_collections(scope=scope, is_enabled=is_enabled)

    return collections


@router.get("/collections/{collection_id}")
async def get_collection(
    collection_id: str,
    session: AsyncSession = Depends(get_session),
) -> KBCollectionResponse:
    """Get KB collection details"""
    kb_service = KBService(session)

    collection = await kb_service.get_collection(collection_id)

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return collection


@router.delete("/collections/{collection_id}")
async def delete_collection(
    collection_id: str,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Delete KB collection"""
    kb_service = KBService(session)

    success = await kb_service.delete_collection(collection_id)

    if not success:
        raise HTTPException(status_code=404, detail="Collection not found")

    return SuccessResponse(success=True)


@router.post("/collections/{collection_id}/documents", status_code=201)
@limiter.limit(RATE_LIMITS["kb_mutations"])
async def import_document(
    request: Request,
    collection_id: str,
    title: str,
    doc_type: str,
    file_path: str,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Import a document into KB collection"""
    kb_service = KBService(session)

    doc_id = await kb_service.import_document(
        collection_id=collection_id,
        title=title,
        doc_type=doc_type,
        file_path=file_path,
    )

    return SuccessResponse(success=True, id=doc_id)
