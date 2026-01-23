"""
Metrics routes for evaluation dashboard
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_session
from ..database.models import PrecheckTask, Risk
from ..schemas.pydantic_models import (
    F1ScoreResponse,
    HallucinationRateResponse,
    MetricsOverviewResponse,
)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/overview")
async def get_metrics_overview(
    from_date: str = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., alias="to", description="End date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_session),
) -> MetricsOverviewResponse:
    """Get metrics overview for a date range"""

    # Parse dates
    start_dt = datetime.fromisoformat(from_date)
    end_dt = datetime.fromisoformat(to_date) + timedelta(days=1)  # Include end date

    # Total tasks
    total_tasks_result = await session.execute(
        select(func.count(PrecheckTask.id)).where(
            PrecheckTask.created_at >= start_dt, PrecheckTask.created_at < end_dt
        )
    )
    total_tasks = total_tasks_result.scalar() or 0

    # Completed tasks
    completed_tasks_result = await session.execute(
        select(func.count(PrecheckTask.id)).where(
            PrecheckTask.created_at >= start_dt,
            PrecheckTask.created_at < end_dt,
            PrecheckTask.status == "DONE",
        )
    )
    completed_tasks = completed_tasks_result.scalar() or 0

    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Average duration
    avg_duration_result = await session.execute(
        select(
            func.avg(
                func.julianday(PrecheckTask.updated_at) - func.julianday(PrecheckTask.created_at)
            ) * 86400
        ).where(
            PrecheckTask.created_at >= start_dt,
            PrecheckTask.created_at < end_dt,
            PrecheckTask.status == "DONE",
        )
    )
    avg_duration_seconds = avg_duration_result.scalar() or 0

    # Risk distribution
    risk_dist_result = await session.execute(
        select(Risk.risk_level, func.count(Risk.id))
        .join(PrecheckTask, Risk.task_id == PrecheckTask.id)
        .where(
            PrecheckTask.created_at >= start_dt,
            PrecheckTask.created_at < end_dt,
        )
        .group_by(Risk.risk_level)
    )
    risk_rows = risk_dist_result.all()
    risk_distribution = {
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    for level, count in risk_rows:
        if level in risk_distribution:
            risk_distribution[level] = count

    # Daily breakdown
    daily_breakdown = []
    current_dt = start_dt
    while current_dt < end_dt:
        day_start = current_dt
        day_end = current_dt + timedelta(days=1)

        created_result = await session.execute(
            select(func.count(PrecheckTask.id)).where(
                PrecheckTask.created_at >= day_start, PrecheckTask.created_at < day_end
            )
        )
        tasks_created = created_result.scalar() or 0

        completed_result = await session.execute(
            select(func.count(PrecheckTask.id)).where(
                PrecheckTask.created_at >= day_start,
                PrecheckTask.created_at < day_end,
                PrecheckTask.status == "DONE",
            )
        )
        tasks_completed = completed_result.scalar() or 0

        daily_breakdown.append(
            {
                "date": current_dt.strftime("%Y-%m-%d"),
                "tasks_created": tasks_created,
                "tasks_completed": tasks_completed,
            }
        )

        current_dt += timedelta(days=1)

    return MetricsOverviewResponse(
        period={"start": from_date, "end": to_date},
        total_tasks=total_tasks,
        completion_rate=completion_rate,
        avg_duration_seconds=avg_duration_seconds,
        risk_distribution=risk_distribution,
        daily_breakdown=daily_breakdown,
    )


@router.get("/f1-score")
async def get_f1_score(session: AsyncSession = Depends(get_session)) -> F1ScoreResponse:
    """Get F1 score metrics (placeholder values for now)"""
    # TODO: Implement actual F1 score calculation based on test cases
    # For now, return placeholder values
    return F1ScoreResponse(
        f1_score=85.2,
        precision=88.5,
        recall=82.1,
    )


@router.get("/hallucination-rate")
async def get_hallucination_rate(
    session: AsyncSession = Depends(get_session),
) -> HallucinationRateResponse:
    """Get hallucination rate (placeholder values for now)"""
    # TODO: Implement actual hallucination rate calculation
    # For now, return placeholder values
    return HallucinationRateResponse(
        rate=3.2,
        trend=-0.5,
    )
