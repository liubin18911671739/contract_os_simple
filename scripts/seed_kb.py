#!/usr/bin/env python3
"""
Seed Knowledge Base Script
Populates the KB with sample legal documents from test-data
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func, select
from server.database.connection import get_session_maker
from server.database.models import KBCollection, KBChunk, KBDocument, KBEmbedding
from server.services.kb_service import KBService
from server.utils.file_parser import parse_file


# Default KB collections to create
DEFAULT_COLLECTIONS = [
    {
        "name": "合同法律法规",
        "scope": "GLOBAL",
        "description": "中国合同相关法律法规知识库",
    },
    {
        "name": "标准合同模板",
        "scope": "GLOBAL",
        "description": "各类标准合同模板参考",
    },
    {
        "name": "风险检查规则",
        "scope": "GLOBAL",
        "description": "合同风险检查规则和指南",
    },
]

# Sample documents to import (relative to test-data/contracts)
SAMPLE_DOCUMENTS = [
    {
        "collection": "合同法律法规",
        "title": "劳动合同法相关条款",
        "doc_type": "regulation",
        "files": ["劳动合同.txt"],
    },
    {
        "collection": "标准合同模板",
        "title": "技术服务合同模板",
        "doc_type": "template",
        "files": ["技术服务合同.txt"],
    },
    {
        "collection": "标准合同模板",
        "title": "销售合同模板",
        "doc_type": "template",
        "files": ["销售合同.txt"],
    },
    {
        "collection": "标准合同模板",
        "title": "保密协议模板",
        "doc_type": "template",
        "files": ["保密协议.txt"],
    },
]


async def create_default_collections(session_maker) -> dict:
    """
    Create default KB collections

    Returns:
        Dict mapping collection names to IDs
    """
    print("Creating default KB collections...")

    collection_map = {}

    async with session_maker() as session:
        kb_service = KBService(session)

        for col_config in DEFAULT_COLLECTIONS:
            # Check if collection already exists
            existing = await session.execute(
                select(KBCollection).where(KBCollection.name == col_config["name"])
            )
            existing_col = existing.scalar_one_or_none()

            if existing_col:
                print(f"  - Collection '{col_config['name']}' already exists (ID: {existing_col.id})")
                collection_map[col_config["name"]] = existing_col.id
            else:
                col_id = await kb_service.create_collection(
                    name=col_config["name"],
                    scope=col_config["scope"],
                )
                print(f"  + Created collection: {col_config['name']} (ID: {col_id})")
                collection_map[col_config["name"]] = col_id

    return collection_map


async def import_documents(session_maker, collection_map: dict, test_data_dir: Path):
    """
    Import sample documents into KB collections

    Args:
        session_maker: Database session maker
        collection_map: Dict mapping collection names to IDs
        test_data_dir: Path to test-data directory
    """
    print("\nImporting sample documents...")

    contracts_dir = test_data_dir / "contracts"

    if not contracts_dir.exists():
        print(f"  Warning: Contracts directory not found: {contracts_dir}")
        return

    async with session_maker() as session:
        kb_service = KBService(session)

        for doc_config in SAMPLE_DOCUMENTS:
            collection_name = doc_config["collection"]
            collection_id = collection_map.get(collection_name)

            if not collection_id:
                print(f"  - Skipping '{doc_config['title']}': Collection '{collection_name}' not found")
                continue

            for filename in doc_config["files"]:
                file_path = contracts_dir / filename

                if not file_path.exists():
                    print(f"  - File not found: {filename}")
                    continue

                # Determine MIME type from extension
                ext = file_path.suffix.lower()
                mime_map = {
                    ".txt": "text/plain",
                    ".md": "text/plain",
                    ".pdf": "application/pdf",
                    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                }
                content_type = mime_map.get(ext, "text/plain")

                # Read and parse file
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()

                    text = parse_file(content, content_type)

                    if not text or not text.strip():
                        print(f"  - Skipping '{filename}': No text content")
                        continue

                    # Import to KB
                    doc_id = await kb_service.import_text(
                        collection_id=collection_id,
                        title=f"{doc_config['title']} - {filename}",
                        doc_type=doc_config["doc_type"],
                        text=text,
                        object_key=f"test-data/contracts/{filename}",
                    )

                    print(f"  + Imported: {filename} -> {collection_name} (chunks: ~{len(text) // 500})")

                except Exception as e:
                    print(f"  - Failed to import '{filename}': {e}")


async def show_kb_status(session_maker):
    """Display current KB status"""
    print("\n" + "=" * 50)
    print("Knowledge Base Status")
    print("=" * 50)

    async with session_maker() as session:
        # Count collections
        collections_result = await session.execute(select(func.count(KBCollection.id)))
        collection_count = collections_result.scalar() or 0

        # Count documents
        docs_result = await session.execute(select(func.count(KBDocument.id)))
        doc_count = docs_result.scalar() or 0

        # Count chunks
        chunks_result = await session.execute(select(func.count(KBChunk.id)))
        chunk_count = chunks_result.scalar() or 0

        # Count indexed chunks
        indexed_result = await session.execute(select(func.count(KBEmbedding.chunk_id)))
        indexed_count = indexed_result.scalar() or 0

        print(f"\nCollections: {collection_count}")
        print(f"Documents:   {doc_count}")
        print(f"Chunks:      {chunk_count}")
        print(f"Indexed:     {indexed_count}")

        # List collections with document counts
        print("\nCollections:")
        collections_query = select(KBCollection).order_by(KBCollection.name)
        collections = (await session.execute(collections_query)).scalars().all()

        for col in collections:
            # Count documents in this collection
            doc_count_query = select(func.count(KBDocument.id)).where(
                KBDocument.collection_id == col.id
            )
            col_doc_count = (await session.execute(doc_count_query)).scalar() or 0

            # Count indexed chunks in this collection
            chunk_count_query = (
                select(func.count(KBChunk.id))
                .join(KBEmbedding, KBChunk.id == KBEmbedding.chunk_id)
                .join(KBDocument, KBChunk.document_id == KBDocument.id)
                .where(KBDocument.collection_id == col.id)
            )
            col_indexed = (await session.execute(chunk_count_query)).scalar() or 0

            status = "✓" if col_indexed > 0 else "○"
            print(f"  [{status}] {col.name}: {col_doc_count} docs, ~{col_indexed} indexed chunks")

    print("=" * 50)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Seed knowledge base with sample data")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Recreate collections if they already exist",
    )
    parser.add_argument(
        "--test-data",
        type=str,
        default="test-data",
        help="Path to test-data directory (default: test-data)",
    )
    parser.add_argument(
        "--status-only",
        "-s",
        action="store_true",
        help="Only show KB status, don't import anything",
    )

    args = parser.parse_args()

    test_data_dir = Path(args.test_data)

    if args.status_only:
        session_maker = get_session_maker()
        await show_kb_status(session_maker)
        return

    print("=" * 50)
    print("KB Seeding Script")
    print("=" * 50)
    print(f"Test data directory: {test_data_dir.absolute()}")

    session_maker = get_session_maker()

    # Create collections
    collection_map = await create_default_collections(session_maker)

    # Import documents
    await import_documents(session_maker, collection_map, test_data_dir)

    # Show status
    await show_kb_status(session_maker)

    print("\n✓ KB seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
