"""
Dashboard routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from ..database.connection import get_session
from ..database.models import PrecheckTask, Contract, KBCollection
from ..schemas.pydantic_models import DashboardStatsResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session),
) -> DashboardStatsResponse:
    """Get dashboard statistics"""

    # Count tasks by status
    total_tasks_result = await session.execute(
        select(func.count(PrecheckTask.id))
    )
    total_tasks = total_tasks_result.scalar() or 0

    active_tasks_result = await session.execute(
        select(func.count(PrecheckTask.id)).where(
            PrecheckTask.status.in_(["QUEUED", "PROCESSING"])
        )
    )
    active_tasks = active_tasks_result.scalar() or 0

    completed_tasks_result = await session.execute(
        select(func.count(PrecheckTask.id)).where(
            PrecheckTask.status == "COMPLETED"
        )
    )
    completed_tasks = completed_tasks_result.scalar() or 0

    failed_tasks_result = await session.execute(
        select(func.count(PrecheckTask.id)).where(
            PrecheckTask.status == "FAILED"
        )
    )
    failed_tasks = failed_tasks_result.scalar() or 0

    # Count contracts
    total_contracts_result = await session.execute(
        select(func.count(Contract.id))
    )
    total_contracts = total_contracts_result.scalar() or 0

    # Count KB collections
    total_kb_result = await session.execute(
        select(func.count(KBCollection.id))
    )
    total_kb_collections = total_kb_result.scalar() or 0

    return DashboardStatsResponse(
        total_tasks=total_tasks,
        active_tasks=active_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        total_contracts=total_contracts,
        total_kb_collections=total_kb_collections,
    )
