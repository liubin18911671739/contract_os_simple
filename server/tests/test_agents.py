"""
Tests for Agent classes
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from server.agents.parse_agent import ParseAgent
from server.agents.split_agent import SplitAgent
from server.agents.stub_agents import RulesAgent


@pytest.mark.asyncio
async def test_parse_agent(test_db, sample_contract_text):
    """Test ParseAgent contract parsing"""
    # Create test contract
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
        version_number=1,
        file_path="test.txt",
    )
    test_db.add(version)

    # Mock file service to return sample text
    with patch("server.agents.parse_agent.FileService") as mock_fs:
        mock_fs.return_value.get_file_content.return_value = sample_contract_text.encode()

        agent = ParseAgent(test_db)
        result = await agent.execute(version_id, {})

    assert result is not None
    assert "contract_version_id" in result or "text_length" in result


@pytest.mark.asyncio
async def test_split_agent(test_db):
    """Test SplitAgent clause splitting"""
    from server.database.models import ContractVersion
    import uuid

    version_id = f"version_{uuid.uuid4().hex[:12]}"
    version = ContractVersion(
        id=version_id,
        contract_id=f"contract_{uuid.uuid4().hex[:12]}",
        version_number=1,
        file_path="test.txt",
    )
    test_db.add(version)

    # Create task
    from server.database.models import PrecheckTask, ConfigSnapshot

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
        status="PARSING",
        progress=12,
        current_stage="STRUCTURING",
        kb_mode="STRICT",
    )
    test_db.add(task)

    # Mock contract text
    contract_text = """
    Clause 1: Services

    The Developer shall provide software development services.

    Clause 2: Payment

    Client shall pay Developer $50,000.

    Clause 3: Termination

    Either party may terminate upon 30 days notice.
    """

    with patch("server.agents.split_agent.FileService") as mock_fs:
        mock_fs.return_value.get_file_content.return_value = contract_text.encode()

        agent = SplitAgent(test_db)
        result = await agent.execute(task_id, {})

    assert result is not None
    assert "clause_count" in result
    assert result["clause_count"] > 0


@pytest.mark.asyncio
async def test_rules_agent(test_db):
    """Test RulesAgent keyword matching"""
    from server.database.models import PrecheckTask, ContractVersion, ConfigSnapshot, Clause
    import uuid

    # Setup
    version_id = f"version_{uuid.uuid4().hex[:12]}"
    version = ContractVersion(
        id=version_id,
        contract_id=f"contract_{uuid.uuid4().hex[:12]}",
        version_number=1,
        file_path="test.txt",
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
        status="STRUCTURING",
        progress=25,
        current_stage="RULE_SCORING",
        kb_mode="STRICT",
    )
    test_db.add(task)

    # Create test clauses
    clause1_id = f"clause_{uuid.uuid4().hex[:12]}"
    clause1 = Clause(
        id=clause1_id,
        task_id=task_id,
        clause_id=clause1_id,
        title="Liability",
        text="The parties agree to unlimited liability for all damages.",
        order_no=1,
    )
    test_db.add(clause1)

    clause2_id = f"clause_{uuid.uuid4().hex[:12]}"
    clause2 = Clause(
        id=clause2_id,
        task_id=task_id,
        clause_id=clause2_id,
        title="Termination",
        text="This contract will automatically renew every year.",
        order_no=2,
    )
    test_db.add(clause2)

    await test_db.commit()

    # Execute agent
    agent = RulesAgent(test_db)
    result = await agent.execute(task_id, {})

    assert result is not None
    assert "rule_hits_count" in result
    # Should find "unlimited liability" and "automatically renew"
    assert result["rule_hits_count"] >= 2
