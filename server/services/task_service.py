"""
Task Service
Manages precheck task lifecycle
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import fetch_all_sql, fetch_one_sql
from ..database.models import (Clause, ConfigSnapshot, Contract,
                               ContractVersion, PrecheckTask, Risk, TaskEvent,
                               TaskKBSnapshot)


class TaskService:
    """Precheck task management service"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        contract_version_id: str,
        kb_collection_ids: List[str],
        kb_mode: str = "STRICT",
        template_id: Optional[str] = None,
    ) -> str:
        """
        Create a new precheck task

        Args:
            contract_version_id: Contract version to analyze
            kb_collection_ids: List of KB collection IDs to use
            kb_mode: KB retrieval mode (STRICT or RELAXED)
            template_id: Optional report template ID

        Returns:
            Task ID
        """
        # Create config snapshot
        config_snapshot_id = f"cfg_{uuid.uuid4().hex[:12]}"
        config_snapshot = ConfigSnapshot(
            id=config_snapshot_id,
            ruleset_version="v1.0",
            model_config_json={
                "chat_model": "glm-4-flash",
                "embed_model": "embedding-3",
            },
            prompt_template_version="v1.0",
            kb_collection_versions_json={col_id: 1 for col_id in kb_collection_ids},
        )
        self.session.add(config_snapshot)
        await self.session.flush()  # Flush to ensure config_snapshot gets its ID

        # Create task
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task = PrecheckTask(
            id=task_id,
            contract_version_id=contract_version_id,
            status="QUEUED",
            progress=0,
            current_stage="QUEUED",
            config_snapshot_id=config_snapshot_id,
            cancel_requested=False,
            kb_mode=kb_mode,
        )
        self.session.add(task)

        # Create KB snapshots
        for col_id in kb_collection_ids:
            snapshot = TaskKBSnapshot(
                id=f"kb_snap_{uuid.uuid4().hex[:12]}",
                task_id=task_id,
                collection_id=col_id,
                collection_version=1,
            )
            self.session.add(snapshot)

        # Log initial event
        event = TaskEvent(
            id=f"event_{uuid.uuid4().hex[:12]}",
            task_id=task_id,
            stage="QUEUED",
            level="info",
            message="Task created and queued",
        )
        self.session.add(event)

        await self.session.commit()

        return task_id

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task details

        Args:
            task_id: Task ID

        Returns:
            Task dict or None
        """
        query = (
            select(
                PrecheckTask.id,
                PrecheckTask.status,
                PrecheckTask.progress,
                PrecheckTask.current_stage,
                PrecheckTask.error_message,
                PrecheckTask.cancel_requested,
                PrecheckTask.kb_mode,
                PrecheckTask.created_at,
                PrecheckTask.updated_at,
                Contract.contract_name,
            )
            .select_from(PrecheckTask)
            .join(
                ContractVersion, PrecheckTask.contract_version_id == ContractVersion.id
            )
            .join(Contract, ContractVersion.contract_id == Contract.id)
            .where(PrecheckTask.id == task_id)
        )

        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return None

        return {
            "id": row[0],
            "status": row[1],
            "progress": row[2],
            "current_stage": row[3],
            "error_message": row[4],
            "cancel_requested": row[5],
            "kb_mode": row[6],
            "created_at": row[7].isoformat(),
            "updated_at": row[8].isoformat(),
            "contract_name": row[9],
        }

    async def list_tasks(
        self,
        page: int = 1,
        limit: int = 10,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "DESC",
    ) -> Dict[str, Any]:
        """
        List tasks with pagination

        Args:
            page: Page number (1-indexed)
            limit: Items per page
            status: Filter by status
            sort_by: Sort field
            sort_order: Sort order (ASC or DESC)

        Returns:
            Dict with tasks, total, page, limit
        """
        from sqlalchemy.orm import selectinload

        # Count query
        count_query = select(func.count(PrecheckTask.id))
        if status:
            count_query = count_query.where(PrecheckTask.status == status)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar()

        # Main query with eager loading to avoid MissingGreenlet issues
        query = (
            select(PrecheckTask)
            .options(
                selectinload(PrecheckTask.contract_version).selectinload(
                    ContractVersion.contract
                )
            )
        )

        if status:
            query = query.where(PrecheckTask.status == status)

        # Sorting
        sort_column = getattr(PrecheckTask, sort_by, PrecheckTask.created_at)
        if sort_order.upper() == "DESC":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Pagination
        offset = (page - 1) * limit
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        task_objects = result.scalars().all()

        # Build response
        tasks = []
        for task in task_objects:
            contract_name = "Unknown"
            if task.contract_version and task.contract_version.contract:
                contract_name = task.contract_version.contract.contract_name

            tasks.append(
                {
                    "id": task.id,
                    "status": task.status,
                    "progress": task.progress,
                    "current_stage": task.current_stage,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "contract_name": contract_name,
                    "error_message": task.error_message,
                    "cancel_requested": task.cancel_requested or False,
                    "kb_mode": task.kb_mode or "STRICT",
                }
            )

        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def update_task_progress(
        self,
        task_id: str,
        stage: str,
        progress: int,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """
        Update task progress

        Args:
            task_id: Task ID
            stage: Current stage name
            progress: Progress percentage (0-100)
            status: New status (optional)
            error_message: Error message if failed
        """
        task = await self.session.get(PrecheckTask, task_id)
        if task:
            task.current_stage = stage
            task.progress = progress
            if status:
                task.status = status
            if error_message:
                task.error_message = error_message
            task.updated_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def log_event(
        self,
        task_id: str,
        stage: str,
        level: str,
        message: str,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a task event

        Args:
            task_id: Task ID
            stage: Current stage
            level: Log level (info, warning, error)
            message: Log message
            meta: Optional metadata
        """
        event = TaskEvent(
            id=f"event_{uuid.uuid4().hex[:12]}",
            task_id=task_id,
            stage=stage,
            level=level,
            message=message,
            meta_json=meta or {},
        )
        self.session.add(event)
        await self.session.commit()

    async def get_task_events(self, task_id: str) -> List[Dict[str, Any]]:
        """Get task events"""
        query = (
            select(TaskEvent)
            .where(TaskEvent.task_id == task_id)
            .order_by(TaskEvent.ts.asc())
        )

        result = await self.session.execute(query)
        events = result.scalars().all()

        return [
            {
                "id": event.id,
                "ts": event.ts.isoformat(),
                "stage": event.stage,
                "level": event.level,
                "message": event.message,
                "meta": event.meta_json,
            }
            for event in events
        ]

    async def set_cancel_requested(self, task_id: str):
        """Request task cancellation"""
        task = await self.session.get(PrecheckTask, task_id)
        if task:
            task.cancel_requested = True
            await self.session.commit()

    async def is_cancel_requested(self, task_id: str) -> bool:
        """Check if cancellation was requested"""
        task = await self.session.get(PrecheckTask, task_id)
        return task.cancel_requested if task else False

    async def get_task_kb_collections(self, task_id: str) -> List[str]:
        """Get KB collection IDs for a task"""
        query = select(TaskKBSnapshot.collection_id).where(
            TaskKBSnapshot.task_id == task_id
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [row[0] for row in rows]

    async def get_task_summary(self, task_id: str) -> Dict[str, Any]:
        """Get task summary statistics"""
        # Use raw SQL for complex aggregation
        query = """
            SELECT
                COUNT(DISTINCT c.id) as clause_count,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'HIGH') as high_risks,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'MEDIUM') as medium_risks,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'LOW') as low_risks,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'INFO') as info_risks
            FROM precheck_tasks pt
            LEFT JOIN clauses c ON c.task_id = pt.id
            LEFT JOIN risks r ON r.task_id = pt.id
            WHERE pt.id = ?
            GROUP BY pt.id
        """

        result = await fetch_one_sql(query, (task_id,))

        if result:
            return {
                "clause_count": result["clause_count"] or 0,
                "high_risks": result["high_risks"] or 0,
                "medium_risks": result["medium_risks"] or 0,
                "low_risks": result["low_risks"] or 0,
                "info_risks": result["info_risks"] or 0,
            }

        return {
            "clause_count": 0,
            "high_risks": 0,
            "medium_risks": 0,
            "low_risks": 0,
            "info_risks": 0,
        }

    async def get_task_clauses(
        self,
        task_id: str,
        risk_level: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get task clauses with associated risks"""
        query = (
            select(
                Clause.id,
                Clause.clause_id,
                Clause.title,
                Clause.text,
                Clause.order_no,
                Risk.id.label("risk_id"),
                Risk.risk_level,
                Risk.summary,
                Risk.status,
            )
            .select_from(Clause)
            .outerjoin(
                Risk,
                and_(
                    Risk.clause_id == Clause.clause_id, Risk.task_id == Clause.task_id
                ),
            )
            .where(Clause.task_id == task_id)
        )

        if risk_level:
            query = query.where(Risk.risk_level == risk_level)

        if search_query:
            pattern = f"%{search_query}%"
            query = query.where(
                Clause.text.ilike(pattern) | Clause.title.ilike(pattern)
            )

        query = query.order_by(Clause.order_no)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "id": row.id,
                "clause_id": row.clause_id,
                "title": row.title,
                "text": row.text,
                "order_no": row.order_no,
                "risk_id": row.risk_id,
                "risk_level": row.risk_level,
                "risk_summary": row.summary,
                "risk_status": row.status,
            }
            for row in rows
        ]

    async def delete_task(self, task_id: str, force: bool = False) -> bool:
        """
        Delete a task and all its related data

        Args:
            task_id: Task ID to delete
            force: If True, skip running task check and attempt to cancel

        Returns:
            True if deleted, False if not found
        """
        from sqlalchemy import delete as sql_delete

        # Check if task exists
        task = await self.session.get(PrecheckTask, task_id)
        if not task:
            return False

        # Check if task is running
        if task.status in ("QUEUED", "PROCESSING"):
            if not force:
                raise ValueError(
                    "Cannot delete a running task. Use force=True to cancel and delete."
                )
            # Try to cancel the task first
            task.cancel_requested = True
            await self.session.commit()

        # Store config snapshot id before deletion
        config_snapshot_id = task.config_snapshot_id

        # Delete in order of dependencies (child records first)
        # 1. Delete KB snapshots
        await self.session.execute(
            sql_delete(TaskKBSnapshot).where(TaskKBSnapshot.task_id == task_id)
        )

        # 2. Delete rule hits
        from ..database.models import RuleHit

        await self.session.execute(
            sql_delete(RuleHit).where(RuleHit.risk_id.in_(
                select(Risk.id).where(Risk.task_id == task_id)
            ))
        )

        # 3. Delete KB hits (temp)
        from ..database.models import KBHitTemp

        await self.session.execute(
            sql_delete(KBHitTemp).where(KBHitTemp.task_id == task_id)
        )

        # 4. Delete KB citations
        from ..database.models import KBCitation

        await self.session.execute(
            sql_delete(KBCitation).where(KBCitation.risk_id.in_(
                select(Risk.id).where(Risk.task_id == task_id)
            ))
        )

        # 5. Delete evidences
        from ..database.models import Evidence

        await self.session.execute(
            sql_delete(Evidence).where(Evidence.risk_id.in_(
                select(Risk.id).where(Risk.task_id == task_id)
            ))
        )

        # 6. Delete risks
        await self.session.execute(
            sql_delete(Risk).where(Risk.task_id == task_id)
        )

        # 7. Delete clauses
        await self.session.execute(
            sql_delete(Clause).where(Clause.task_id == task_id)
        )

        # 8. Delete task events
        await self.session.execute(
            sql_delete(TaskEvent).where(TaskEvent.task_id == task_id)
        )

        # 9. Delete reviews
        from ..database.models import Review

        await self.session.execute(
            sql_delete(Review).where(Review.task_id == task_id)
        )

        # 10. Delete the task using raw SQL to avoid ORM cascade issues
        await self.session.execute(
            sql_delete(PrecheckTask).where(PrecheckTask.id == task_id)
        )

        await self.session.commit()

        # 11. Delete config snapshot after task is deleted (using a new session to avoid issues)
        if config_snapshot_id:
            from ..database.connection import get_session_maker
            session_maker = get_session_maker()
            async with session_maker() as new_session:
                config_snapshot = await new_session.get(ConfigSnapshot, config_snapshot_id)
                if config_snapshot:
                    await new_session.delete(config_snapshot)
                    await new_session.commit()

        return True
