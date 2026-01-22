"""
Knowledge Base Service
Manages KB collections, documents, chunks, and embeddings
"""
import hashlib
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import (
    KBCollection,
    KBDocument,
    KBChunk,
    KBEmbedding,
)
from ..config import settings, get_storage_path
from .llm_service import get_llm_service
from ..utils.vector_store import get_vector_store


class KBService:
    """Knowledge base management service"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.llm_service = get_llm_service()

    async def create_collection(
        self,
        name: str,
        scope: str = "GLOBAL",
    ) -> str:
        """
        Create a new KB collection

        Args:
            name: Collection name
            scope: Collection scope (GLOBAL, TENANT, PROJECT, DEPT)

        Returns:
            Collection ID
        """
        collection_id = f"kb_col_{uuid.uuid4().hex[:12]}"

        collection = KBCollection(
            id=collection_id,
            name=name,
            scope=scope,
            version=1,
            is_enabled=True,
        )

        self.session.add(collection)
        await self.session.commit()

        return collection_id

    async def list_collections(
        self,
        scope: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        List KB collections

        Args:
            scope: Filter by scope
            is_enabled: Filter by enabled status

        Returns:
            List of collections
        """
        query = select(KBCollection)

        if scope:
            query = query.where(KBCollection.scope == scope)
        if is_enabled is not None:
            query = query.where(KBCollection.is_enabled == is_enabled)

        query = query.order_by(KBCollection.created_at.desc())

        result = await self.session.execute(query)
        collections = result.scalars().all()

        return [
            {
                "id": col.id,
                "name": col.name,
                "scope": col.scope,
                "version": col.version,
                "is_enabled": col.is_enabled,
                "created_at": col.created_at.isoformat(),
            }
            for col in collections
        ]

    async def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get collection by ID"""
        collection = await self.session.get(KBCollection, collection_id)

        if not collection:
            return None

        # Get document count
        doc_count_query = select(KBDocument).where(
            KBDocument.collection_id == collection_id
        )
        result = await self.session.execute(doc_count_query)
        doc_count = len(result.scalars().all())

        return {
            "id": collection.id,
            "name": collection.name,
            "scope": collection.scope,
            "version": collection.version,
            "is_enabled": collection.is_enabled,
            "document_count": doc_count,
            "created_at": collection.created_at.isoformat(),
        }

    async def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a collection and all its data

        Args:
            collection_id: Collection ID

        Returns:
            True if deleted, False if not found
        """
        collection = await self.session.get(KBCollection, collection_id)

        if not collection:
            return False

        # Delete from DB (cascade will handle documents, chunks)
        await self.session.delete(collection)
        await self.session.commit()

        # Delete Faiss index
        vector_store = get_vector_store(collection_id)
        vector_store.delete()

        return True

    async def import_document(
        self,
        collection_id: str,
        title: str,
        doc_type: str,
        file_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> str:
        """
        Import a document into KB

        Args:
            collection_id: Target collection ID
            title: Document title
            doc_type: Document type (regulation, guideline, etc.)
            file_path: Path to document file
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks

        Returns:
            Document ID
        """
        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Calculate hash
        file_hash = hashlib.sha256(text.encode()).hexdigest()

        # Check if document already exists
        existing_query = select(KBDocument).where(
            and_(
                KBDocument.collection_id == collection_id,
                KBDocument.hash == file_hash,
            )
        )
        result = await self.session.execute(existing_query)
        existing = result.scalar_one_or_none()

        if existing:
            return existing.id

        # Create document record
        doc_id = f"kb_doc_{uuid.uuid4().hex[:12]}"
        document = KBDocument(
            id=doc_id,
            collection_id=collection_id,
            title=title,
            doc_type=doc_type,
            object_key=file_path,  # For simplicity, store path
            version=1,
            hash=file_hash,
        )

        self.session.add(document)
        await self.session.flush()

        # Split text into chunks
        chunks = self._split_text(text, chunk_size, chunk_overlap)

        # Create chunk records
        chunk_records = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"kb_chunk_{uuid.uuid4().hex[:12]}"
            chunk = KBChunk(
                id=chunk_id,
                document_id=doc_id,
                chunk_no=i,
                text=chunk_text,
                meta_json={
                    "title": title,
                    "chunk_count": len(chunks),
                },
            )
            chunk_records.append(chunk)
            self.session.add(chunk)

        await self.session.commit()

        # Generate embeddings
        await self._embed_and_index_chunks(doc_id, chunks)

        # Increment collection version
        collection = await self.session.get(KBCollection, collection_id)
        if collection:
            collection.version += 1
            await self.session.commit()

        return doc_id

    def _split_text(
        self, text: str, chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        """Split text into chunks"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < text_len:
                last_period = chunk.rfind("。")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > chunk_size // 2:
                    chunk = text[start : start + break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - chunk_overlap

        return chunks

    async def _embed_and_index_chunks(self, doc_id: str, chunks: List[str]):
        """Generate embeddings and index chunks"""
        # Get chunk IDs
        query = select(KBChunk).where(KBChunk.document_id == doc_id)
        result = await self.session.execute(query)
        chunk_records = result.scalars().all()

        chunk_ids = [chunk.id for chunk in chunk_records]
        chunk_texts = [chunk.text for chunk in chunk_records]

        # Generate embeddings (batch)
        embeddings = await self.llm_service.embed(chunk_texts)

        # Store in Faiss
        # Get collection ID from first chunk
        if chunk_ids:
            # Get document to find collection
            doc = await self.session.get(KBDocument, doc_id)
            if doc:
                vector_store = get_vector_store(doc.collection_id)
                vector_store.add_vectors(embeddings, chunk_ids)

                # Create embedding records
                for chunk_id in chunk_ids:
                    embedding = KBEmbedding(chunk_id=chunk_id)
                    self.session.add(embedding)

                await self.session.commit()

                # Save index
                vector_store.save()

    async def search_chunks(
        self,
        collection_id: str,
        query: str,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks

        Args:
            collection_id: Collection to search
            query: Query text
            top_k: Number of results

        Returns:
            List of chunks with scores
        """
        # Generate query embedding
        query_vector = await self.llm_service.embed_single(query)

        # Search Faiss index
        vector_store = get_vector_store(collection_id)
        results = vector_store.search(query_vector, top_k)

        # Fetch chunk details
        chunk_ids = [chunk_id for chunk_id, _ in results]
        score_map = {chunk_id: score for chunk_id, score in results}

        if not chunk_ids:
            return []

        query = select(KBChunk).where(KBChunk.id.in_(chunk_ids))
        result = await self.session.execute(query)
        chunks = result.scalars().all()

        # Build response
        chunk_map = {chunk.id: chunk for chunk in chunks}
        output = []

        for chunk_id, score in results:
            if chunk_id in chunk_map:
                chunk = chunk_map[chunk_id]
                output.append({
                    "chunk_id": chunk.id,
                    "text": chunk.text,
                    "score": score,
                    "meta": chunk.meta_json,
                })

        return output

    async def rerank_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_n: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks using ZhipuAI Rerank-2

        Args:
            query: Query text
            chunks: List of chunk dicts with 'text' field
            top_n: Number of top results

        Returns:
            Reranked chunks
        """
        return await self.llm_service.rerank(query, chunks, top_n)
