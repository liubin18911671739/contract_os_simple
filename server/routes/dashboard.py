"""
Dashboard routes
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.connection import get_session
from ..database.models import (
    Contract,
    ContractVersion,
    KBCollection,
    PrecheckTask,
    Risk,
)
from ..schemas.pydantic_models import (
    DashboardStatsResponse,
    RecentTaskResponse,
    RecentTasksResponse,
    TrendsData,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session),
) -> DashboardStatsResponse:
    """Get dashboard statistics"""

    # Count total contracts (completed tasks)
    total_contracts_result = await session.execute(
        select(func.count(PrecheckTask.id)).where(PrecheckTask.status == "DONE")
    )
    total_contracts = total_contracts_result.scalar() or 0

    # Count high risk findings
    high_risk_result = await session.execute(
        select(func.count(Risk.id))
        .join(PrecheckTask, Risk.task_id == PrecheckTask.id)
        .where(PrecheckTask.status == "DONE", Risk.risk_level == "HIGH")
    )
    high_risk_findings = high_risk_result.scalar() or 0

    # Calculate compliance rate (tasks with no high risks / total completed)
    # For simplicity, count tasks that don't have HIGH risks
    if total_contracts > 0:
        tasks_with_high_risks_result = await session.execute(
            select(func.count(PrecheckTask.id))
            .join(Risk, Risk.task_id == PrecheckTask.id)
            .where(PrecheckTask.status == "DONE", Risk.risk_level == "HIGH")
            .distinct()
        )
        tasks_with_high_risks = tasks_with_high_risks_result.scalar() or 0
        tasks_without_high_risks = total_contracts - tasks_with_high_risks
        compliance_rate = int((tasks_without_high_risks / total_contracts) * 100)
    else:
        compliance_rate = 100  # Default to 100% when no data

    # Calculate average processing time (in seconds)
    avg_time_result = await session.execute(
        select(
            func.avg(
                func.julianday(PrecheckTask.updated_at) - func.julianday(PrecheckTask.created_at)
            ) * 86400
        ).where(PrecheckTask.status == "DONE")
    )
    avg_processing_time = avg_time_result.scalar() or 0

    # Calculate 7-day trends
    seven_days_ago = datetime.now() - timedelta(days=7)

    # Contracts analyzed in last 7 days
    contracts_7d_result = await session.execute(
        select(func.count(PrecheckTask.id)).where(
            PrecheckTask.status == "DONE",
            PrecheckTask.created_at >= seven_days_ago,
        )
    )
    contracts_analyzed_7d = contracts_7d_result.scalar() or 0

    # High risks discovered in last 7 days
    risks_7d_result = await session.execute(
        select(func.count(Risk.id))
        .join(PrecheckTask, Risk.task_id == PrecheckTask.id)
        .where(
            Risk.risk_level == "HIGH",
            PrecheckTask.created_at >= seven_days_ago,
        )
    )
    risk_discovery_7d = risks_7d_result.scalar() or 0

    # Compliance rate for last 7 days
    total_7d = contracts_analyzed_7d
    if total_7d > 0:
        tasks_with_high_risks_7d_result = await session.execute(
            select(func.count(PrecheckTask.id))
            .join(Risk, Risk.task_id == PrecheckTask.id)
            .where(
                PrecheckTask.status == "DONE",
                PrecheckTask.created_at >= seven_days_ago,
                Risk.risk_level == "HIGH",
            )
            .distinct()
        )
        tasks_with_high_risks_7d = tasks_with_high_risks_7d_result.scalar() or 0
        tasks_without_high_risks_7d = total_7d - tasks_with_high_risks_7d
        compliance_rate_7d = int((tasks_without_high_risks_7d / total_7d) * 100)
    else:
        compliance_rate_7d = 0

    return DashboardStatsResponse(
        total_contracts=total_contracts,
        high_risk_findings=high_risk_findings,
        compliance_rate=compliance_rate,
        avg_processing_time=avg_processing_time,
        trends_7d=TrendsData(
            contracts_analyzed=contracts_analyzed_7d,
            risk_discovery=risk_discovery_7d,
            compliance_rate=compliance_rate_7d,
        ),
    )


@router.get("/recent-tasks")
async def get_recent_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> RecentTasksResponse:
    """Get recent tasks for dashboard"""

    # Count total
    total_result = await session.execute(select(func.count(PrecheckTask.id)))
    total = total_result.scalar() or 0

    # Get tasks with pagination - eagerly load contract_version and contract
    offset = (page - 1) * limit
    tasks_result = await session.execute(
        select(PrecheckTask)
        .options(
            selectinload(PrecheckTask.contract_version).selectinload(
                # type: ignore[attr-defined]
                ContractVersion.contract
            )
        )
        .order_by(PrecheckTask.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    tasks = tasks_result.scalars().all()

    # Get risk counts for each task
    task_ids = [task.id for task in tasks]
    high_risk_counts: dict[str, int] = {}
    medium_risk_counts: dict[str, int] = {}

    if task_ids:
        risk_counts_result = await session.execute(
            select(Risk.task_id, Risk.risk_level, func.count(Risk.id))
            .where(Risk.task_id.in_(task_ids))
            .group_by(Risk.task_id, Risk.risk_level)
        )
        for task_id, level, count in risk_counts_result.all():
            if level == "HIGH":
                high_risk_counts[task_id] = count
            elif level == "MEDIUM":
                medium_risk_counts[task_id] = count

    # Build response
    recent_tasks = []
    for task in tasks:
        # Get contract name from version relationship
        contract_name = "Unknown"
        if task.contract_version and task.contract_version.contract:
            contract_name = task.contract_version.contract.contract_name

        recent_tasks.append(
            RecentTaskResponse(
                id=task.id,
                contract_name=contract_name,
                status=task.status,
                progress=task.progress,
                created_at=task.created_at.isoformat(),
                high_risks=high_risk_counts.get(task.id, 0),
                medium_risks=medium_risk_counts.get(task.id, 0),
            )
        )

    return RecentTasksResponse(
        tasks=recent_tasks,
        total=total,
        page=page,
        limit=limit,
    )
