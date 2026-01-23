"""
Test configuration and fixtures
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

# Set test environment variables BEFORE importing server modules
os.environ.setdefault("ZHIPU_API_KEY", "test_key_for_unit_tests")
os.environ.setdefault("DATABASE_PATH", "/tmp/test_db.db")
os.environ.setdefault("STORAGE_ROOT", "/tmp/test_storage")

# Add project root to Python path
# This allows importing from server package when running pytest from project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from server.config import Settings
from server.database.models import Base


@pytest.fixture(scope="function")
async def test_db():
    """Create a temporary test database"""
    # Create temporary database file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        db_path = f.name

    # Create test engine
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session maker
    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()
    os.unlink(db_path)


@pytest.fixture(scope="function")
def test_settings():
    """Create test settings"""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = Settings(
            zhipu_api_key="test_key",
            database_path=os.path.join(tmpdir, "test.db"),
            storage_root=tmpdir,
            host="localhost",
            port=8001,
            cors_origins=["http://localhost:3000"],
            max_concurrent_tasks=2,
            max_api_concurrent=3,
            enable_rate_limit=False,  # Disable rate limiting in tests
        )
        yield settings


@pytest.fixture
def sample_contract_text():
    """Sample contract text for testing"""
    return """
    SOFTWARE DEVELOPMENT AGREEMENT

    This Software Development Agreement ("Agreement") is entered into as of January 1, 2024,

    BETWEEN:
    Client ABC Inc., a corporation organized under the laws of California, USA

    AND
    Developer XYZ LLC, a software development company

    1. SERVICES

    The Developer shall provide software development services as described in Exhibit A.
    The Developer warrants that all services will be performed in a professional manner.

    2. COMPENSATION

    Client shall pay Developer the sum of $50,000 for the services.
    Payment shall be made within 30 days of invoice.

    3. LIABILITY

    The Developer shall not be liable for any indirect or consequential damages.
    The Client's sole remedy shall be limited to the refund of fees paid.

    4. TERMINATION

    Either party may terminate this Agreement upon 30 days written notice.
    The Client may terminate for convenience with a termination fee equal to 50% of remaining fees.

    5. CONFIDENTIALITY

    Both parties agree to keep confidential all proprietary information shared during the term.
    This obligation shall survive termination of this Agreement.

    6. GOVERNING LAW

    This Agreement shall be governed by the laws of the State of California.
    Any disputes shall be resolved through binding arbitration.
    """


@pytest.fixture
def sample_kb_document():
    """Sample KB document for testing"""
    return """
    # Software Contract Risk Guidelines

    ## Liability Limitations

    Software development contracts should always include liability limitations.
    Recommended caps: 1-2x the contract value.

    ## Termination Clauses

    Fair termination provisions should include:
    - Termination for cause with cure period
    - Termination for convenience with reasonable fees
    - No automatic renewal without explicit consent

    ## Payment Terms

    Best practices:
    - Net 30 payment terms
    - Late payment penalties: 1.5% per month
    - Milestone-based payments for long projects
    """
