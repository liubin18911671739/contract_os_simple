"""
Clear all data from the database
This script deletes all records from all tables while keeping the schema intact.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from server.config import settings


TABLES_TO_CLEAR = [
    # Child tables first (due to foreign key constraints)
    "suggestion_revisions",
    "suggestions",
    "kb_citations",
    "kb_hits_temp",
    "kb_embeddings",
    "kb_chunks",
    "kb_documents",
    "kb_collections",
    "evidences",
    "rule_hits",
    "risks",
    "clauses",
    "task_events",
    "task_kb_snapshots",
    "reviews",
    "reports",
    "precheck_tasks",
    "config_snapshots",
    "contract_versions",
    "contracts",
    "audit_logs",
]


async def clear_database():
    """Clear all data from all tables"""
    db_path = settings.database_path

    print(f"Connecting to database: {db_path}")

    # Create async engine
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    async with engine.begin() as conn:
        # Enable foreign keys
        await conn.execute(text("PRAGMA foreign_keys = ON"))

        # Get counts before clearing
        print("\n=== Data before clearing ===")
        for table in TABLES_TO_CLEAR:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            if count > 0:
                print(f"  {table}: {count} records")

        print("\n=== Clearing data ===")

        # Clear each table
        for table in TABLES_TO_CLEAR:
            try:
                result = await conn.execute(text(f"DELETE FROM {table}"))
                print(f"  Cleared {table}: {result.rowcount} records")
            except Exception as e:
                print(f"  Error clearing {table}: {e}")

        # Verify all tables are empty
        print("\n=== Verification ===")
        all_empty = True
        for table in TABLES_TO_CLEAR:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            if count > 0:
                print(f"  WARNING: {table} still has {count} records")
                all_empty = False

        if all_empty:
            print("  All tables are empty!")

    await engine.dispose()
    print("\n=== Database cleared successfully ===")


if __name__ == "__main__":
    asyncio.run(clear_database())
