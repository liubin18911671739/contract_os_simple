"""
Knowledge Base routes
"""

import hashlib
import logging
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
                                       KBDocumentResponse, SuccessResponse,
                                       KBSearchRequest, KBSearchResultResponse,
                                       KBChunkResponse, KBCollectionStatsResponse)
from ..services.file_service import FileService
from ..services.kb_service import KBService
from ..utils.file_parser import parse_file

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])
logger = logging.getLogger(__name__)


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
    """Upload a document to a KB collection with automatic chunking and embedding"""
    # Verify collection exists
    collection_result = await session.execute(
        select(KBCollection).where(KBCollection.id == collection_id)
    )
    collection = collection_result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Read file content
    content = await file.read()

    # Extract text from file based on content type
    content_type = file.content_type or ""
    filename = file.filename or ""

    # Map filename extension to MIME type if content_type is missing
    if not content_type or content_type == "application/octet-stream":
        ext = Path(filename).suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".md": "text/plain",
        }
        content_type = mime_map.get(ext, "text/plain")

    # Parse file content to extract text
    try:
        text = parse_file(content, content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse file: {str(e)}"
        )

    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text content found in file"
        )

    # Optionally save original file
    file_service = FileService()
    file_service.ensure_storage_dirs()

    file_hash = hashlib.sha256(content).hexdigest()[:16]
    ext = Path(filename).suffix or ".txt"
    safe_filename = f"{file_hash}{ext}"

    try:
        object_key = file_service.save_file("kb_documents", safe_filename, content)
    except Exception as e:
        logger.error(f"Failed to save KB document file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save document file: {str(e)}"
        )

    # Use KBService.import_text to handle chunking and embedding
    kb_service = KBService(session)

    doc_id = await kb_service.import_text(
        collection_id=collection_id,
        title=title,
        doc_type=doc_type,
        text=text,
        object_key=object_key,
    )

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


@router.post("/search")
async def search_knowledge_base(
    request: KBSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> list[KBSearchResultResponse]:
    """Search knowledge base using vector similarity with reranking"""
    kb_service = KBService(session)

    # Get all enabled collections if none specified
    collection_ids = request.collection_ids if request.collection_ids else None

    try:
        # Search for relevant chunks
        chunks = await kb_service.search_chunks(
            collection_ids=collection_ids,
            query=request.query,
            top_k=request.top_k,
        )

        # Apply reranking if we have results
        if chunks:
            try:
                chunks = await kb_service.rerank_chunks(
                    query=request.query,
                    chunks=chunks,
                    top_n=request.top_k,
                )
            except Exception as e:
                logger.warning(f"Reranking failed, returning original results: {e}")

        # Build response with document metadata
        response = []
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "")
            score = chunk.get("_rerank_score", chunk.get("score", 0))
            text = chunk.get("text", "")
            meta = chunk.get("meta", {})

            # Get document info
            doc_id = meta.get("doc_id")
            doc_title = meta.get("title", "Unknown Document")
            doc_version = chunk.get("doc_version", 1)
            collection_id = meta.get("collection_id")

            # Truncate text for preview
            preview_text = text[:500] if len(text) > 500 else text

            response.append(
                KBSearchResultResponse(
                    chunk_id=chunk_id,
                    text=preview_text,
                    score=float(score),
                    doc_title=doc_title,
                    doc_version=doc_version,
                    doc_id=doc_id,
                    collection_id=collection_id,
                )
            )

        return response

    except Exception as e:
        logger.error(f"KB search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/documents/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[KBChunkResponse]:
    """Get all chunks for a document"""
    from ..database.models import KBChunk, KBEmbedding

    # Get chunks
    chunks_result = await session.execute(
        select(KBChunk)
        .where(KBChunk.document_id == doc_id)
        .order_by(KBChunk.chunk_index)
    )
    chunks = chunks_result.scalars().all()

    # Check which chunks are indexed
    indexed_chunks_result = await session.execute(
        select(KBEmbedding.chunk_id)
        .where(KBEmbedding.chunk_id.in_([c.id for c in chunks]))
    )
    indexed_chunk_ids = set(row[0] for row in indexed_chunks_result.fetchall())

    return [
        KBChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            is_indexed=chunk.id in indexed_chunk_ids,
            created_at=chunk.created_at.isoformat(),
        )
        for chunk in chunks
    ]


@router.get("/chunks/{chunk_id}")
async def get_chunk(
    chunk_id: str,
    session: AsyncSession = Depends(get_session),
) -> KBChunkResponse:
    """Get a specific chunk by ID"""
    from ..database.models import KBChunk, KBEmbedding

    chunk = await session.get(KBChunk, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    # Check if indexed
    embedding_result = await session.execute(
        select(KBEmbedding).where(KBEmbedding.chunk_id == chunk_id)
    )
    is_indexed = embedding_result.scalar_one_or_none() is not None

    return KBChunkResponse(
        id=chunk.id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        is_indexed=is_indexed,
        created_at=chunk.created_at.isoformat(),
    )


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Delete a document and all its chunks"""
    from ..database.models import KBChunk, KBDocument, KBEmbedding
    from sqlalchemy import delete

    # Check if document exists
    doc = await session.get(KBDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    collection_id = doc.collection_id

    # Delete embeddings and chunks (cascade should handle this, but let's be explicit)
    # First delete embeddings for chunks in this document
    chunks_result = await session.execute(
        select(KBChunk.id).where(KBChunk.document_id == doc_id)
    )
    chunk_ids = [row[0] for row in chunks_result.fetchall()]

    if chunk_ids:
        await session.execute(
            delete(KBEmbedding).where(KBEmbedding.chunk_id.in_(chunk_ids))
        )

    # Delete chunks
    await session.execute(
        delete(KBChunk).where(KBChunk.document_id == doc_id)
    )

    # Delete document
    await session.delete(doc)
    await session.commit()

    # Rebuild Faiss index for this collection
    kb_service = KBService(session)
    try:
        await kb_service.rebuild_index(collection_id)
    except Exception as e:
        logger.warning(f"Failed to rebuild index after document deletion: {e}")

    return SuccessResponse(success=True)


@router.get("/collections/{collection_id}/stats")
async def get_collection_stats(
    collection_id: str,
    session: AsyncSession = Depends(get_session),
) -> KBCollectionStatsResponse:
    """Get detailed statistics for a collection"""
    from ..database.models import KBCollection, KBChunk, KBDocument, KBEmbedding

    collection = await session.get(KBCollection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Count documents
    doc_count_result = await session.execute(
        select(func.count(KBDocument.id)).where(KBDocument.collection_id == collection_id)
    )
    document_count = doc_count_result.scalar() or 0

    # Count chunks
    chunk_count_result = await session.execute(
        select(func.count(KBChunk.id))
        .join(KBDocument, KBDocument.id == KBChunk.document_id)
        .where(KBDocument.collection_id == collection_id)
    )
    chunk_count = chunk_count_result.scalar() or 0

    # Count indexed chunks
    indexed_count_result = await session.execute(
        select(func.count(KBEmbedding.chunk_id))
        .join(KBChunk, KBChunk.id == KBEmbedding.chunk_id)
        .join(KBDocument, KBDocument.id == KBChunk.document_id)
        .where(KBDocument.collection_id == collection_id)
    )
    indexed_count = indexed_count_result.scalar() or 0

    # Calculate average chunk size
    avg_size_result = await session.execute(
        select(func.avg(func.length(KBChunk.text)))
        .join(KBDocument, KBDocument.id == KBChunk.document_id)
        .where(KBDocument.collection_id == collection_id)
    )
    avg_chunk_size = avg_size_result.scalar() or 0

    # Calculate storage (rough estimate)
    total_storage_mb = (chunk_count * avg_chunk_size) / (1024 * 1024)

    return KBCollectionStatsResponse(
        id=collection.id,
        name=collection.name,
        document_count=document_count,
        chunk_count=chunk_count,
        indexed_count=indexed_count,
        avg_chunk_size=float(avg_chunk_size),
        total_storage_mb=round(total_storage_mb, 2),
    )


@router.get("/cache-stats")
async def get_cache_stats() -> dict:
    """Get embedding cache statistics for monitoring"""
    from ..services.kb_service import get_cache_stats
    return get_cache_stats()

