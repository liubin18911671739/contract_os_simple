#!/usr/bin/env python3
"""
Initialize the database and create tables
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.database.connection import init_db, close_db
from server.config import settings, get_db_path


async def main():
    """Initialize database"""
    print(f"Initializing database at: {get_db_path()}")

    # Ensure data directory exists
    get_db_path().parent.mkdir(parents=True, exist_ok=True)
    Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
    (Path(settings.storage_root) / "contracts").mkdir(exist_ok=True)
    (Path(settings.storage_root) / "kb_documents").mkdir(exist_ok=True)
    (Path(settings.storage_root) / "reports").mkdir(exist_ok=True)

    # Initialize database tables
    await init_db()
    print("✓ Database tables created successfully")

    # Close connections
    await close_db()
    print("✓ Database initialization complete")


if __name__ == "__main__":
    asyncio.run(main())
