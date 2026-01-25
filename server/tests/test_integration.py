"""
Integration tests for the complete task pipeline.

These tests run the full 8-stage pipeline from task creation to completion,
testing the integration between orchestrator, agents, and services.
"""

import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Set test environment variables BEFORE importing server modules
os.environ.setdefault("ZHIPU_API_KEY", "test_key_for_unit_tests")
os.environ.setdefault("DATABASE_PATH", "/tmp/test_db.db")
os.environ.setdefault("STORAGE_ROOT", "/tmp/test_storage")

import sys
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from server.agents.stub_agents import (EvidenceAgent, KBRetrievalAgent,
                                         QCAgent, RulesAgent)
from server.agents.parse_agent import ParseAgent
from server.agents.split_agent import SplitAgent
from server.agents.report_agent import ReportAgent
from server.config import Settings
from server.database.models import (Base, Clause, PrecheckTask, Risk,
                                     TaskEvent)
from server.orchestrator import TaskOrchestrator
from server.services.contract_service import ContractService
from server.services.task_service import TaskService


@pytest.fixture(scope="function")
async def integration_db():
    """Create a temporary test database with all tables

    Note: Uses the configured DATABASE_PATH so that agents using fetch_all_sql()
    connect to the same database.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from server.config import get_db_path

    # Use the configured database path so fetch_all_sql() connects to same DB
    db_path = get_db_path()

    # Remove existing test database if it exists
    if db_path.exists():
        os.unlink(db_path)

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        yield session

    await engine.dispose()

    # Clean up test database
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def test_contract_data():
    """Create test contract data - returns both path and content bytes"""
    content = """
        SOFTWARE DEVELOPMENT AGREEMENT

        This Agreement is entered into as of January 1, 2024.

        BETWEEN:
        Client ABC Inc. and Developer XYZ LLC.

        1. SERVICES
        Developer shall provide software development services.

        2. COMPENSATION
        Client shall pay Developer $50,000.

        3. LIABILITY
        Developer shall not be liable for indirect damages.
        Client's sole remedy is refund of fees.

        4. TERMINATION
        Either party may terminate upon 30 days notice.
        Client may terminate for convenience with 50% fee.

        5. CONFIDENTIALITY
        Both parties agree to keep information confidential.

        6. GOVERNING LAW
        This Agreement is governed by California law.
    """
    return content.encode("utf-8")


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service that returns realistic responses"""
    from server.services.llm_service import LLMService

    mock = MagicMock(spec=LLMService)

    # Mock chat_with_json to return risk analysis
    async def mock_chat_with_json(messages, temperature=0.3):
        return {
            "risks": [
                {
                    "risk_level": "HIGH",
                    "risk_type": "LIABILITY",
                    "confidence": 0.85,
                    "summary": "责任限制条款过于苛刻，仅退款费用不足以覆盖间接损失",
                    "kb_evidence": []
                },
                {
                    "risk_level": "MEDIUM",
                    "risk_type": "TERMINATION",
                    "confidence": 0.70,
                    "summary": "终止条款规定了30天通知期，但便利终止费用过高",
                    "kb_evidence": []
                }
            ]
        }

    # Mock embed_single to return a dummy embedding
    async def mock_embed_single(text):
        # Return a 1024-dim embedding (typical for embedding-3)
        return [0.1] * 1024

    # Mock embed for batch calls
    async def mock_embed(texts):
        return [[0.1] * 1024 for _ in texts]

    # Mock rerank to return input chunks
    async def mock_rerank(query, documents, top_n=6):
        return documents[:top_n]

    mock.chat_with_json = mock_chat_with_json
    mock.embed_single = mock_embed_single
    mock.embed = mock_embed
    mock.rerank = mock_rerank

    return mock


@pytest.mark.asyncio
async def test_full_task_pipeline(integration_db, test_contract_data, mock_llm_service):
    """
    Test the complete 8-stage task pipeline:
    1. Create contract and upload version
    2. Create precheck task
    3. Run through all stages
    4. Verify final results
    """
    # Setup services
    contract_service = ContractService(integration_db)
    task_service = TaskService(integration_db)

    # Step 1: Create contract
    contract_id = await contract_service.create_contract(
        contract_name="Test Software Agreement",
        counterparty="Client ABC Inc.",
        contract_type="SOFTWARE_DEVELOPMENT",
    )
    assert contract_id is not None
    print(f"[1/8] Created contract: {contract_id}")

    # Step 2: Upload contract version
    version_result = await contract_service.upload_contract_version(
        contract_id=contract_id,
        file_content=test_contract_data,
        filename="test_contract.txt",
        mime_type="text/plain",
    )
    version_id = version_result["id"]
    assert version_id is not None
    print(f"[2/8] Uploaded version: {version_id}")

    # Step 3: Create precheck task (without KB for simplicity)
    task_id = await task_service.create_task(
        contract_version_id=version_id,
        kb_collection_ids=[],
        kb_mode="RELAXED",
    )
    assert task_id is not None
    print(f"[3/8] Created task: {task_id}")

    # Step 4: Run orchestrator through all stages (with mocked LLM)
    # Import here to reset the global LLM service before the test
    from server.services import llm_service as llm_service_module

    # Reset the global LLM service to None so it picks up our mock
    llm_service_module._llm_service = None

    payload = {}
    stage_results = {}

    # Stage 1: PARSING
    parse_agent = ParseAgent(integration_db)
    result = await parse_agent.execute(task_id, payload)
    stage_results["PARSING"] = result
    payload.update(result)
    print(f"[4/8] Stage PARSING completed")

    # Verify file was parsed
    task_check = await integration_db.get(PrecheckTask, task_id)
    assert task_check is not None

    # Stage 2: STRUCTURING
    split_agent = SplitAgent(integration_db)
    result = await split_agent.execute(task_id, payload)
    stage_results["STRUCTURING"] = result
    payload.update(result)
    print(f"[4/8] Stage STRUCTURING completed")

    # Verify clauses were created
    clauses_result = await integration_db.execute(
        select(Clause).where(Clause.task_id == task_id)
    )
    clauses = clauses_result.scalars().all()
    assert len(clauses) > 0
    print(f"[4/8] Created {len(clauses)} clauses")

    # Stage 3: RULE_SCORING
    rules_agent = RulesAgent(integration_db)
    result = await rules_agent.execute(task_id, payload)
    stage_results["RULE_SCORING"] = result
    payload.update(result)
    print(f"[4/8] Stage RULE_SCORING completed")

    # Stage 4: KB_RETRIEVAL (skip if no KB collections)
    kb_agent = KBRetrievalAgent(integration_db)
    result = await kb_agent.execute(task_id, payload)
    stage_results["KB_RETRIEVAL"] = result
    payload.update(result)
    print(f"[4/8] Stage KB_RETRIEVAL completed")

    # Import LLMRiskAgent here to avoid circular import
    from server.agents.llm_risk_agent import LLMRiskAgent

    # Stage 5: LLM_RISK - inject mock LLM service directly
    llm_agent = LLMRiskAgent(integration_db)
    # Replace the agent's LLM service with our mock
    llm_agent.llm_service = mock_llm_service
    result = await llm_agent.execute(task_id, payload)
    stage_results["LLM_RISK"] = result
    payload.update(result)
    print(f"[4/8] Stage LLM_RISK completed")

    # Verify risks were created
    risks_result = await integration_db.execute(
        select(Risk).where(Risk.task_id == task_id)
    )
    risks = risks_result.scalars().all()
    assert len(risks) > 0
    print(f"[4/8] Created {len(risks)} risks")

    # Stage 6: EVIDENCING
    evidence_agent = EvidenceAgent(integration_db)
    result = await evidence_agent.execute(task_id, payload)
    stage_results["EVIDENCING"] = result
    payload.update(result)
    print(f"[4/8] Stage EVIDENCING completed")

    # Stage 7: QCING
    qc_agent = QCAgent(integration_db)
    result = await qc_agent.execute(task_id, payload)
    stage_results["QCING"] = result
    payload.update(result)
    print(f"[4/8] Stage QCING completed")

    # Stage 8: DONE
    report_agent = ReportAgent(integration_db)
    result = await report_agent.execute(task_id, payload)
    stage_results["DONE"] = result
    payload.update(result)
    print(f"[4/8] Stage DONE completed")

    # Step 5: Verify final task state
    final_task = await integration_db.get(PrecheckTask, task_id)

    assert final_task.status == "COMPLETED"
    assert final_task.progress == 100
    assert final_task.current_stage == "DONE"
    assert final_task.error_message is None
    print(f"[5/8] Task completed successfully")

    # Step 6: Verify all data was created correctly
    # Check clauses
    clauses_result = await integration_db.execute(
        select(Clause).where(Clause.task_id == task_id)
    )
    clauses = clauses_result.scalars().all()
    assert len(clauses) >= 5  # At least 5 clauses from our test contract

    # Check risks
    risks_result = await integration_db.execute(
        select(Risk).where(Risk.task_id == task_id)
    )
    risks = risks_result.scalars().all()
    assert len(risks) >= 2  # At least 2 risks from mocked LLM

    # Check risk levels - with mock we should get HIGH and MEDIUM
    risk_levels = {r.risk_level for r in risks}
    assert "HIGH" in risk_levels
    assert "MEDIUM" in risk_levels

    # Check events were logged
    events_result = await integration_db.execute(
        select(TaskEvent).where(TaskEvent.task_id == task_id)
    )
    events = events_result.scalars().all()
    assert len(events) >= 8  # At least one event per stage

    print(f"[6/8] All verifications passed!")
    print(f"\n=== Integration Test Summary ===")
    print(f"Task ID: {task_id}")
    print(f"Clauses: {len(clauses)}")
    print(f"Risks: {len(risks)}")
    print(f"Events: {len(events)}")
    print(f"Status: {final_task.status}")
    print(f"Progress: {final_task.progress}%")
    print(f"=============================\n")


@pytest.mark.asyncio
async def test_task_retry_flow(integration_db, test_contract_data):
    """Test retrying a failed task"""
    contract_service = ContractService(integration_db)
    task_service = TaskService(integration_db)

    # Create contract and version
    contract_id = await contract_service.create_contract(
        contract_name="Retry Test",
        counterparty="Test Client",
        contract_type="TEST",
    )
    version_result = await contract_service.upload_contract_version(
        contract_id=contract_id,
        file_content=test_contract_data,
        filename="test.txt",
        mime_type="text/plain",
    )
    version_id = version_result["id"]

    # Create task
    task_id = await task_service.create_task(
        contract_version_id=version_id,
        kb_collection_ids=[],
        kb_mode="RELAXED",
    )

    # Mark task as failed
    await task_service.update_task_progress(
        task_id,
        "LLM_RISK",
        75,
        status="FAILED",
        error_message="Test failure",
    )

    # Get task
    task = await task_service.get_task(task_id)
    assert task["status"] == "FAILED"

    # Reset to QUEUED (simulating retry)
    await task_service.update_task_progress(
        task_id,
        "QUEUED",
        0,
        status="QUEUED",
        error_message=None,
    )

    # Verify reset
    task = await task_service.get_task(task_id)
    assert task["status"] == "QUEUED"
    assert task["error_message"] is None
    assert task["progress"] == 0

    print("Retry flow test passed!")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
