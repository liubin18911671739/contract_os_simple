"""
Task routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_session
from ..orchestrator import get_orchestrator
from ..rate_limit import RATE_LIMITS, limiter
from ..schemas.pydantic_models import (ClauseResponse,
                                       CreatePrecheckTaskRequest,
                                       ErrorResponse, GenerateReportRequest,
                                       SetConclusionRequest, SuccessResponse,
                                       TaskEventResponse, TaskListResponse,
                                       TaskResponse, TaskSummaryResponse)
from ..services.file_service import FileService
from ..services.task_service import TaskService

router = APIRouter(prefix="/api/precheck-tasks", tags=["tasks"])


@router.get("")
async def list_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    status: str = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("DESC"),
    session: AsyncSession = Depends(get_session),
) -> TaskListResponse:
    """List tasks with pagination and filters"""
    task_service = TaskService(session)

    result = await task_service.list_tasks(
        page=page,
        limit=limit,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return result


@router.post("", status_code=201)
@limiter.limit(RATE_LIMITS["create_task"])
async def create_task(
    request: Request,
    data: CreatePrecheckTaskRequest,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Create a new precheck task"""
    task_service = TaskService(session)

    task_id = await task_service.create_task(
        contract_version_id=data.contract_version_id,
        kb_collection_ids=data.kb_collection_ids,
        kb_mode=data.kb_mode,
        template_id=data.template_id,
    )

    # Start orchestrator in background
    orchestrator = get_orchestrator()
    import asyncio

    asyncio.create_task(orchestrator.run_task(task_id))

    return SuccessResponse(success=True, id=task_id)


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Get task details"""
    task_service = TaskService(session)

    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.get("/{task_id}/events")
async def get_task_events(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[TaskEventResponse]:
    """Get task events"""
    task_service = TaskService(session)

    events = await task_service.get_task_events(task_id)

    return events


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Cancel a running task"""
    task_service = TaskService(session)

    # Check if task exists
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if task can be cancelled
    status = task.get("status")
    if status in ("COMPLETED", "FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task with status {status}",
        )

    # Set cancel flag in database
    await task_service.set_cancel_requested(task_id)

    # Notify orchestrator
    orchestrator = get_orchestrator()
    await orchestrator.cancel_task(task_id)

    return SuccessResponse(success=True)


@router.get("/{task_id}/summary")
async def get_task_summary(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> TaskSummaryResponse:
    """Get task summary statistics"""
    task_service = TaskService(session)

    summary = await task_service.get_task_summary(task_id)

    return summary


@router.get("/{task_id}/clauses")
async def get_task_clauses(
    task_id: str,
    risk_level: str = Query(None),
    q: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[ClauseResponse]:
    """Get task clauses with risks"""
    task_service = TaskService(session)

    clauses = await task_service.get_task_clauses(
        task_id, risk_level=risk_level, search_query=q
    )

    return clauses


@router.post("/{task_id}/conclusion")
async def set_task_conclusion(
    task_id: str,
    data: SetConclusionRequest,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Set task conclusion"""
    import uuid

    from ..database.models import Review

    review = Review(
        id=f"review_{uuid.uuid4().hex[:12]}",
        task_id=task_id,
        conclusion=data.conclusion,
        notes=data.notes,
        created_by="user",
    )

    session.add(review)
    await session.commit()

    return SuccessResponse(success=True)


@router.post("/{task_id}/report", status_code=201)
async def generate_report(
    task_id: str,
    data: GenerateReportRequest,
    session: AsyncSession = Depends(get_session),
):
    """Generate task report (returns report info if already exists)"""
    import uuid

    from sqlalchemy import desc, select

    from ..database.models import TaskEvent

    task_service = TaskService(session)
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if report already exists by looking for completion event with report path
    events_query = (
        select(TaskEvent)
        .where(TaskEvent.task_id == task_id)
        .where(TaskEvent.message.like("%Report generated:%"))
        .order_by(desc(TaskEvent.created_at))
        .limit(1)
    )
    result = await session.execute(events_query)
    last_event = result.scalar_one_or_none()

    if last_event and last_event.message:
        # Extract report path from event message
        # Format: "Report generated: reports/report_xxx.html"
        report_path = last_event.message.split("Report generated: ")[-1].strip()
        file_service = FileService()

        if file_service.file_exists(report_path):
            filename = report_path.split("/")[-1]
            return {
                "id": f"report_{uuid.uuid4().hex[:12]}",
                "task_id": task_id,
                "format": data.format,
                "report_path": report_path,
                "download_url": f"/api/precheck-tasks/{task_id}/report/download",
                "filename": filename,
                "status": "completed",
            }

    # If no report exists and task is not complete, return error
    if task.get("status") != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Task not completed yet. Report will be available after completion.",
        )

    # Task completed but no report found (shouldn't happen with new ReportAgent)
    raise HTTPException(
        status_code=404, detail="Report not found. Please run the task again."
    )


@router.get("/{task_id}/report/download")
async def download_report(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Download the generated report file"""
    from sqlalchemy import desc, select

    from ..database.models import TaskEvent

    # Find the most recent report generation event
    events_query = (
        select(TaskEvent)
        .where(TaskEvent.task_id == task_id)
        .where(TaskEvent.message.like("%Report generated:%"))
        .order_by(desc(TaskEvent.created_at))
        .limit(1)
    )
    result = await session.execute(events_query)
    last_event = result.scalar_one_or_none()

    if not last_event:
        raise HTTPException(status_code=404, detail="Report not found for this task")

    # Extract report path from event message
    report_path = last_event.message.split("Report generated: ")[-1].strip()
    file_service = FileService()

    if not file_service.file_exists(report_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    file_path = file_service.get_file_path(report_path)
    filename = report_path.split("/")[-1]

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/html",
        content_disposition_type="attachment",
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Delete a task and all its related data"""
    task_service = TaskService(session)

    try:
        success = await task_service.delete_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return SuccessResponse(success=True)
