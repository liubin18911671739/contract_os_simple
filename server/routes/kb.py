"""
Knowledge Base routes
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Request,
                     UploadFile)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_session
from ..database.models import KBCollection, KBChunk, KBDocument, KBEmbedding
from ..rate_limit import RATE_LIMITS, limiter
from ..schemas.pydantic_models import (CreateKBCollectionRequest,
                                       KBCollectionResponse,
                                       KBDocumentResponse, SuccessResponse)
from ..services.file_service import FileService
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


@router.post("/documents", status_code=201)
@limiter.limit(RATE_LIMITS["kb_mutations"])
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    collection_id: str = Form(...),
    title: str = Form(...),
    doc_type: str = Form(default="txt"),
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Upload a document to a KB collection"""
    # Verify collection exists
    collection_result = await session.execute(
        select(KBCollection).where(KBCollection.id == collection_id)
    )
    collection = collection_result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Save file
    file_service = FileService()
    file_service.ensure_storage_dirs()

    # Generate unique filename
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()[:16]
    ext = Path(file.filename or "file").suffix or ".txt"
    filename = f"{file_hash}{ext}"

    object_key = file_service.save_file("kb_documents", filename, content)

    # Get file hash for database
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Create KB document entry
    doc_id = str(uuid.uuid4())
    doc = KBDocument(
        id=doc_id,
        collection_id=collection_id,
        title=title,
        doc_type=doc_type,
        object_key=object_key,
        hash=sha256_hash,
    )
    session.add(doc)
    await session.commit()

    return SuccessResponse(success=True, id=doc_id)


@router.get("/documents")
async def list_documents(
    collection_id: str = None,
    session: AsyncSession = Depends(get_session),
) -> list[KBDocumentResponse]:
    """List all KB documents"""
    query = select(KBDocument)

    if collection_id:
        query = query.where(KBDocument.collection_id == collection_id)

    query = query.order_by(KBDocument.created_at.desc())

    result = await session.execute(query)
    documents = result.scalars().all()

    response = []
    for doc in documents:
        # Count chunks
        chunk_count_result = await session.execute(
            select(func.count(KBChunk.id)).where(KBChunk.document_id == doc.id)
        )
        chunk_count = chunk_count_result.scalar() or 0

        # Count indexed chunks (those with embeddings)
        indexed_count_result = await session.execute(
            select(func.count(KBEmbedding.chunk_id))
            .join(KBChunk, KBChunk.id == KBEmbedding.chunk_id)
            .where(KBChunk.document_id == doc.id)
        )
        indexed_count = indexed_count_result.scalar() or 0

        # Determine status
        if indexed_count == chunk_count and chunk_count > 0:
            status = "ready"
        elif indexed_count > 0:
            status = "indexing"
        elif chunk_count > 0:
            status = "chunking"
        else:
            status = "pending"

        response.append(
            KBDocumentResponse(
                id=doc.id,
                collection_id=doc.collection_id,
                title=doc.title,
                doc_type=doc.doc_type,
                chunk_count=chunk_count,
                indexed_count=indexed_count,
                status=status,
                created_at=doc.created_at.isoformat(),
            )
        )

    return response
