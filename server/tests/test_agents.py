"""
Tests for Agent classes
"""
import pytest
import uuid

from server.agents.stub_agents import RulesAgent


@pytest.mark.asyncio
async def test_rules_agent(test_db):
    """Test RulesAgent keyword matching"""
    from server.database.models import (
        PrecheckTask, ContractVersion, ConfigSnapshot,
        Clause, Contract
    )

    # Setup contract
    contract_id = f"contract_{uuid.uuid4().hex[:12]}"
    contract = Contract(
        id=contract_id,
        contract_name="Test Contract",
        counterparty="Test Party",
        contract_type="SERVICE",
    )
    test_db.add(contract)

    # Setup contract version
    version_id = f"version_{uuid.uuid4().hex[:12]}"
    version = ContractVersion(
        id=version_id,
        contract_id=contract_id,
        version_no=1,
        object_key="test.txt",
        sha256="abc123",
        mime="text/plain",
    )
    test_db.add(version)

    # Setup config snapshot
    config_id = f"cfg_{uuid.uuid4().hex[:12]}"
    config = ConfigSnapshot(
        id=config_id,
        ruleset_version="v1.0",
        model_config_json={},
        prompt_template_version="v1.0",
        kb_collection_versions_json={},
    )
    test_db.add(config)

    # Setup task
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

