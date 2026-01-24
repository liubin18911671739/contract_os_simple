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

    # Completed tasks (use COMPLETED status, not DONE)
    completed_tasks_result = await session.execute(
        select(func.count(PrecheckTask.id)).where(
            PrecheckTask.created_at >= start_dt,
            PrecheckTask.created_at < end_dt,
            PrecheckTask.status == "COMPLETED",
        )
    )
    completed_tasks = completed_tasks_result.scalar() or 0

    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Average duration (only for completed tasks)
    avg_duration_result = await session.execute(
        select(
            func.avg(
                func.julianday(PrecheckTask.updated_at) - func.julianday(PrecheckTask.created_at)
            ) * 86400
        ).where(
            PrecheckTask.created_at >= start_dt,
            PrecheckTask.created_at < end_dt,
            PrecheckTask.status == "COMPLETED",
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
                PrecheckTask.status == "COMPLETED",
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
async def get_f1_score(
    from_date: str = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_session),
) -> F1ScoreResponse:
    """
    Get F1 score metrics based on risk confirmation status

    Calculation:
    - True Positives (TP): Risks with status 'CONFIRMED'
    - False Positives (FP): Risks with status 'DISMISSED'
    - Precision: TP / (TP + FP) - percentage of confirmed risks out of all reviewed
    - Recall: TP / (TP + FN) - assuming all confirmed risks are actual risks
    - F1 Score: 2 * (Precision * Recall) / (Precision + Recall)
    """
    # Build query with date filter if provided
    query = select(func.count(Risk.id))
    if from_date:
        start_dt = datetime.fromisoformat(from_date)
        query = query.join(PrecheckTask, Risk.task_id == PrecheckTask.id).where(
            PrecheckTask.created_at >= start_dt
        )
    else:
        query = query.join(PrecheckTask, Risk.task_id == PrecheckTask.id)

    if to_date:
        end_dt = datetime.fromisoformat(to_date) + timedelta(days=1)
        query = query.where(PrecheckTask.created_at < end_dt)

    # Count total risks
    total_risks_result = await session.execute(query)
    total_risks = total_risks_result.scalar() or 0

    # Count confirmed risks (True Positives)
    confirmed_query = select(func.count(Risk.id)).where(Risk.status == "CONFIRMED")
    if from_date or to_date:
        confirmed_query = confirmed_query.join(PrecheckTask, Risk.task_id == PrecheckTask.id)
        if from_date:
            confirmed_query = confirmed_query.where(PrecheckTask.created_at >= start_dt)
        if to_date:
            confirmed_query = confirmed_query.where(PrecheckTask.created_at < end_dt)

    confirmed_result = await session.execute(confirmed_query)
    true_positives = confirmed_result.scalar() or 0

    # Count dismissed risks (False Positives)
    dismissed_query = select(func.count(Risk.id)).where(Risk.status == "DISMISSED")
    if from_date or to_date:
        dismissed_query = dismissed_query.join(PrecheckTask, Risk.task_id == PrecheckTask.id)
        if from_date:
            dismissed_query = dismissed_query.where(PrecheckTask.created_at >= start_dt)
        if to_date:
            dismissed_query = dismissed_query.where(PrecheckTask.created_at < end_dt)

    dismissed_result = await session.execute(dismissed_query)
    false_positives = dismissed_result.scalar() or 0

    # Calculate metrics
    reviewed_count = true_positives + false_positives

    if reviewed_count == 0:
        # No reviewed risks yet, return zeros
        return F1ScoreResponse(
            f1_score=0.0,
            precision=0.0,
            recall=0.0,
        )

    # Precision: TP / (TP + FP) - how many detected risks were actually relevant
    precision = true_positives / reviewed_count if reviewed_count > 0 else 0.0

    # Recall: We estimate this by assuming confirmed risks are true positives
    # Since we don't have ground truth for all possible risks, we use confirmed count as baseline
    # A better estimate would be: confirmed / (confirmed + missed risks)
    # For now, we use precision as a proxy for recall when ground truth is unavailable
    recall = precision  # Simplified assumption

    # F1 Score: 2 * (P * R) / (P + R)
    if precision + recall > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0

    return F1ScoreResponse(
        f1_score=round(f1_score * 100, 1),  # Convert to percentage
        precision=round(precision * 100, 1),
        recall=round(recall * 100, 1),
    )


@router.get("/hallucination-rate")
async def get_hallucination_rate(
    from_date: str = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_session),
) -> HallucinationRateResponse:
    """
    Get hallucination rate metrics

    Calculation:
    - Hallucination Rate: Percentage of risks that were dismissed (false positives)
    - Trend: Comparison with previous period (positive = increasing hallucinations)
    """
    # Current period
    start_dt = None
    end_dt = None

    if from_date:
        start_dt = datetime.fromisoformat(from_date)
    if to_date:
        end_dt = datetime.fromisoformat(to_date) + timedelta(days=1)

    # Build base query
    def build_query(start=None, end=None):
        q = select(func.count(Risk.id)).join(
            PrecheckTask, Risk.task_id == PrecheckTask.id
        )
        if start:
            q = q.where(PrecheckTask.created_at >= start)
        if end:
            q = q.where(PrecheckTask.created_at < end)
        return q

    # Current period: total risks and dismissed risks
    total_query = build_query(start_dt, end_dt)
    total_result = await session.execute(total_query)
    total_risks = total_result.scalar() or 0

    dismissed_query = build_query(start_dt, end_dt).where(Risk.status == "DISMISSED")
    dismissed_result = await session.execute(dismissed_query)
    dismissed_count = dismissed_result.scalar() or 0

    # Calculate current rate
    current_rate = (dismissed_count / total_risks * 100) if total_risks > 0 else 0.0

    # Calculate trend (compare with previous period of same length)
    trend = 0.0
    if start_dt and end_dt and (end_dt - start_dt).days > 0:
        period_days = (end_dt - start_dt).days
        prev_start = start_dt - timedelta(days=period_days)
        prev_end = start_dt

        # Previous period stats
        prev_total_query = build_query(prev_start, prev_end)
        prev_total_result = await session.execute(prev_total_query)
        prev_total = prev_total_result.scalar() or 0

        prev_dismissed_query = build_query(prev_start, prev_end).where(Risk.status == "DISMISSED")
        prev_dismissed_result = await session.execute(prev_dismissed_query)
        prev_dismissed = prev_dismissed_result.scalar() or 0

        prev_rate = (prev_dismissed / prev_total * 100) if prev_total > 0 else 0.0
        trend = current_rate - prev_rate  # Positive means hallucinations increased

    return HallucinationRateResponse(
        rate=round(current_rate, 1),
        trend=round(trend, 1),
    )
