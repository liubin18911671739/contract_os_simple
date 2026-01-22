"""
Tests for Task Service
"""
import pytest
import uuid
from sqlalchemy import select

from server.database.models import PrecheckTask, TaskEvent, ConfigSnapshot
from server.services.task_service import TaskService


@pytest.mark.asyncio
async def test_create_task(test_db):
    """Test creating a new task"""
    service = TaskService(test_db)

    # First, create a contract and version
    from server.database.models import Contract, ContractVersion
    import uuid

    contract_id = f"contract_{uuid.uuid4().hex[:12]}"
    contract = Contract(
        id=contract_id,
        contract_name="Test Contract",
        counterparty="Test Party",
        contract_type="SERVICE",
    )
    test_db.add(contract)

    version_id = f"version_{uuid.uuid4().hex[:12]}"
    version = ContractVersion(
        id=version_id,
        contract_id=contract_id,
        version_no=1,
        object_key="test.pdf",
        sha256="abc123",
        mime="application/pdf",
    )
    test_db.add(version)
    await test_db.commit()

    # Create task
    task_id = await service.create_task(
        contract_version_id=version_id,
        kb_collection_ids=["kb_col_1"],
        kb_mode="STRICT",
    )

    assert task_id is not None
    assert task_id.startswith("task_")

    # Verify task was created
    task = await test_db.get(PrecheckTask, task_id)
    assert task is not None
    assert task.status == "QUEUED"
    assert task.progress == 0
    assert task.kb_mode == "STRICT"


@pytest.mark.asyncio
async def test_get_task(test_db):
    """Test getting task details"""
    service = TaskService(test_db)

    # Create test data
    from server.database.models import Contract, ContractVersion, ConfigSnapshot
    import uuid

    contract_id = f"contract_{uuid.uuid4().hex[:12]}"
    contract = Contract(
        id=contract_id,
        contract_name="Test Contract",
        counterparty="Test Party",
        contract_type="SERVICE",
    )
    test_db.add(contract)

    version_id = f"version_{uuid.uuid4().hex[:12]}"
    version = ContractVersion(
        id=version_id,
        contract_id=contract_id,
        version_no=1,
        object_key="test.pdf",
        sha256="abc123",
        mime="application/pdf",
    )
    test_db.add(version)

    config_id = f"cfg_{uuid.uuid4().hex[:12]}"
    config = ConfigSnapshot(
        id=config_id,
        ruleset_version="v1.0",
        model_config_json={},
        prompt_template_version="v1.0",
        kb_collection_versions_json={},
    )
    test_db.add(config)

    task_id = f"task_{uuid.uuid4().hex[:12]}"
    task = PrecheckTask(
        id=task_id,
        contract_version_id=version_id,
        config_snapshot_id=config_id,
        status="RUNNING",
        progress=50,
        current_stage="LLM_RISK",
        kb_mode="STRICT",
    )
    test_db.add(task)
    await test_db.commit()

    # Get task
    result = await service.get_task(task_id)

    assert result is not None
    assert result["id"] == task_id
    assert result["status"] == "RUNNING"
    assert result["progress"] == 50
    assert result["current_stage"] == "LLM_RISK"


@pytest.mark.asyncio
async def test_update_task_progress(test_db):
    """Test updating task progress"""
    service = TaskService(test_db)

    # Create test task
    from server.database.models import Contract, ContractVersion, ConfigSnapshot
    import uuid

    contract_id = f"contract_{uuid.uuid4().hex[:12]}"
    contract = Contract(
        id=contract_id,
        contract_name="Test Contract",
        counterparty="Test Party",
        contract_type="SERVICE",
    )
    test_db.add(contract)

    version_id = f"version_{uuid.uuid4().hex[:12]}"
    version = ContractVersion(
        id=version_id,
        contract_id=contract_id,
        version_no=1,
        object_key="test.pdf",
        sha256="abc123",
        mime="application/pdf",
    )
    test_db.add(version)

    config_id = f"cfg_{uuid.uuid4().hex[:12]}"
    config = ConfigSnapshot(
        id=config_id,
        ruleset_version="v1.0",
        model_config_json={},
        prompt_template_version="v1.0",
        kb_collection_versions_json={},
    )
    test_db.add(config)

    task_id = f"task_{uuid.uuid4().hex[:12]}"
    task = PrecheckTask(
        id=task_id,
        contract_version_id=version_id,
        config_snapshot_id=config_id,
        status="QUEUED",
        progress=0,
        current_stage="QUEUED",
        kb_mode="STRICT",
    )
    test_db.add(task)
    await test_db.commit()

    # Update progress
    await service.update_task_progress(
        task_id,
        stage="PARSING",
        progress=12,
        status="RUNNING",
    )

    # Verify update
    await test_db.refresh(task)
    assert task.current_stage == "PARSING"
    assert task.progress == 12
    assert task.status == "RUNNING"


@pytest.mark.asyncio
async def test_log_event(test_db):
    """Test logging task events"""
    service = TaskService(test_db)

    task_id = f"task_{uuid.uuid4().hex[:12]}"

    # Log event
    await service.log_event(
        task_id,
        stage="PARSING",
        level="info",
        message="Test log message",
        meta={"test": "data"},
    )

    # Verify event was logged
    query = select(TaskEvent).where(TaskEvent.task_id == task_id)
    result = await test_db.execute(query)
    events = result.scalars().all()

    assert len(events) == 1
    assert events[0].stage == "PARSING"
    assert events[0].level == "info"
    assert events[0].message == "Test log message"
    assert events[0].meta_json == {"test": "data"}


@pytest.mark.asyncio
async def test_list_tasks(test_db):
    """Test listing tasks with pagination"""
    service = TaskService(test_db)

    # Create test data
    from server.database.models import Contract, ContractVersion, ConfigSnapshot
    import uuid

    # Create contract
    contract_id = f"contract_{uuid.uuid4().hex[:12]}"
    contract = Contract(
        id=contract_id,
        contract_name="Test Contract",
        counterparty="Test Party",
        contract_type="SERVICE",
    )
    test_db.add(contract)

    version_id = f"version_{uuid.uuid4().hex[:12]}"
    version = ContractVersion(
        id=version_id,
        contract_id=contract_id,
        version_no=1,
        object_key="test.pdf",
        sha256="abc123",
        mime="application/pdf",
    )
    test_db.add(version)

    config_id = f"cfg_{uuid.uuid4().hex[:12]}"
    config = ConfigSnapshot(
        id=config_id,
        ruleset_version="v1.0",
        model_config_json={},
        prompt_template_version="v1.0",
        kb_collection_versions_json={},
    )
    test_db.add(config)

    # Create 15 tasks
    for i in range(15):
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task = PrecheckTask(
            id=task_id,
            contract_version_id=version_id,
            config_snapshot_id=config_id,
            status="COMPLETED" if i < 10 else "RUNNING",
            progress=100 if i < 10 else 50,
            current_stage="DONE" if i < 10 else "PARSING",
            kb_mode="STRICT",
        )
        test_db.add(task)
    await test_db.commit()

    # List tasks (page 1, limit 10)
    result = await service.list_tasks(page=1, limit=10)

    assert result["total"] == 15
    assert len(result["tasks"]) == 10
    assert result["page"] == 1
    assert result["limit"] == 10

    # Filter by status
    result = await service.list_tasks(page=1, limit=10, status="COMPLETED")
    assert result["total"] == 10
    assert len(result["tasks"]) == 10
