#!/usr/bin/env python3
"""
Add missing database indexes for performance optimization.

Run this script to add indexes to an existing database.
If you have a fresh database, the indexes will be created automatically.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from server.database.connection import get_engine, get_session_maker


async def add_indexes():
    """Add missing indexes to existing tables"""
    engine = get_engine()

    # List of indexes to create (table_name, index_name, index_definition)
    indexes = [
        # PrecheckTask indexes
        (
            "precheck_tasks",
            "idx_precheck_tasks_status",
            "CREATE INDEX IF NOT EXISTS idx_precheck_tasks_status ON precheck_tasks (status)",
        ),
        (
            "precheck_tasks",
            "idx_precheck_tasks_status_created",
            "CREATE INDEX IF NOT EXISTS idx_precheck_tasks_status_created ON precheck_tasks (status, created_at)",
        ),
        (
            "precheck_tasks",
            "idx_precheck_tasks_status_updated",
            "CREATE INDEX IF NOT EXISTS idx_precheck_tasks_status_updated ON precheck_tasks (status, updated_at)",
        ),
        # Risk status index
        (
            "risks",
            "idx_risks_status",
            "CREATE INDEX IF NOT EXISTS idx_risks_status ON risks (status)",
        ),
    ]

    async with engine.begin() as conn:
        for table_name, index_name, sql in indexes:
            try:
                # Check if index already exists
                check_sql = f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
                result = await conn.execute(text(check_sql))
                exists = result.fetchone()

                if exists:
                    print(f"[SKIP] Index {index_name} already exists on {table_name}")
                else:
                    await conn.execute(text(sql))
                    print(f"[CREATE] Added index {index_name} on {table_name}")
            except Exception as e:
                print(f"[ERROR] Failed to create index {index_name}: {e}")

    print("\n[OK] Index migration complete!")


async def show_current_indexes():
    """Show all current indexes in the database"""
    engine = get_engine()

    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY tbl_name, name"
            )
        )
        indexes = result.fetchall()

        print("\nCurrent indexes:")
        print("-" * 60)
        current_table = None
        for idx_name, table_name in indexes:
            if table_name != current_table:
                print(f"\n{table_name}:")
                current_table = table_name
            print(f"  - {idx_name}")
        print("-" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database index migration")
    parser.add_argument("--show", action="store_true", help="Show current indexes without modifying")
    args = parser.parse_args()

    if args.show:
        asyncio.run(show_current_indexes())
    else:
        asyncio.run(add_indexes())
        asyncio.run(show_current_indexes())
