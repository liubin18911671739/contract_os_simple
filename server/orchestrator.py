"""
Task Orchestrator
Manages the 8-stage task processing pipeline
Replaces BullMQ with asyncio
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .agents.base import TaskCancelledException
from .agents.llm_risk_agent import LLMRiskAgent
from .agents.parse_agent import ParseAgent
from .agents.report_agent import ReportAgent
from .agents.split_agent import SplitAgent
from .agents.stub_agents import (EvidenceAgent, KBRetrievalAgent, QCAgent,
                                 RulesAgent)
from .config import settings
from .database.connection import get_session_maker
from .database.models import PrecheckTask

# Configure logging
logger = logging.getLogger(__name__)

# Task stages in order with their progress percentages
STAGE_PROGRESS = {
    "QUEUED": 0,
    "PARSING": 12,
    "STRUCTURING": 25,
    "RULE_SCORING": 37,
    "KB_RETRIEVAL": 50,
    "LLM_RISK": 75,
    "EVIDENCING": 87,
    "QCING": 95,
    "DONE": 100,
}

# Task stages in order
STAGE_ORDER = list(STAGE_PROGRESS.keys())

# Agent classes for each stage
AGENT_CLASSES = {
    "PARSING": ParseAgent,
    "STRUCTURING": SplitAgent,
    "RULE_SCORING": RulesAgent,
    "KB_RETRIEVAL": KBRetrievalAgent,
    "LLM_RISK": LLMRiskAgent,
    "EVIDENCING": EvidenceAgent,
    "QCING": QCAgent,
    "DONE": ReportAgent,
}


class TaskOrchestrator:
    """Orchestrates task processing through all stages with concurrency control"""

    # Class variables for tracking cancelled/deleted tasks across instances
    _cancelled_tasks: set[str] = set()
    _deleted_tasks: set[str] = set()

    def __init__(self, max_concurrent_tasks: int | None = None):
        self.running_tasks: Dict[str, asyncio.Task] = {}
        # Semaphore for limiting concurrent tasks
        self.max_concurrent = max_concurrent_tasks or settings.max_concurrent_tasks
        self.task_semaphore = asyncio.Semaphore(self.max_concurrent)
        logger.info(
            f"TaskOrchestrator initialized with max_concurrent={self.max_concurrent}"
        )

    @property
    def cancelled_tasks(self) -> set[str]:
        """Get the cancelled tasks set (class-level for global access)"""
        return TaskOrchestrator._cancelled_tasks

    @property
    def deleted_tasks(self) -> set[str]:
        """Get the deleted tasks set (class-level for global access)"""
        return TaskOrchestrator._deleted_tasks

    async def run_task(self, task_id: str):
        """
        Run a task through all stages with concurrency control

        Args:
            task_id: Task ID to process
        """
        if task_id in self.running_tasks:
            logger.warning(f"Task {task_id} is already running")
            return

        # Create background task with semaphore control
        async def _run_with_semaphore():
            async with self.task_semaphore:
                logger.info(
                    f"Task {task_id} started (active: {len(self.running_tasks)}/{self.max_concurrent})"
                )
                try:
                    await self._process_task(task_id)
                finally:
                    logger.info(f"Task {task_id} completed")

        task = asyncio.create_task(_run_with_semaphore())
        self.running_tasks[task_id] = task

        # Cleanup when done
        def cleanup(t):
            self.running_tasks.pop(task_id, None)
            TaskOrchestrator._cancelled_tasks.discard(task_id)
            TaskOrchestrator._deleted_tasks.discard(task_id)
            logger.debug(f"Task {task_id} cleaned up from running tasks")

        task.add_done_callback(cleanup)

    async def _process_task(self, task_id: str):
        """
        Internal method to process task through stages

        Args:
            task_id: Task ID
        """
        from .services.task_service import TaskService

        session_maker = get_session_maker()
        task_start = time.time()
        stage_times = {}

        async with session_maker() as session:
            payload: Dict[str, Any] = {}
            task_service = TaskService(session)

            try:
                logger.info(
                    f"Task {task_id}: Starting processing through {len(STAGE_ORDER) - 1} stages"
                )

                # Set initial progress to 5% to show task has started
                await task_service.update_task_progress(task_id, "QUEUED", 5)

                # Process each stage
                for i, stage in enumerate(STAGE_ORDER[1:], 1):  # Skip QUEUED
                    stage_start = time.time()

                    # Check if cancelled or deleted
                    if task_id in self.cancelled_tasks:
                        logger.info(
                            f"Task {task_id}: Cancel requested at stage {stage}"
                        )
                        # Check if task was deleted (don't update DB if it was deleted)
                        if task_id not in self.deleted_tasks:
                            await self._mark_cancelled(session, task_id)
                        return

                    # Get stage progress percentage
                    stage_progress = STAGE_PROGRESS.get(stage, 50)

                    # Update progress at stage start to show movement
                    await task_service.update_task_progress(task_id, stage, stage_progress)
                    logger.info(
                        f"Task {task_id}: [Stage {i}/{len(STAGE_ORDER)-1}] {stage} ({stage_progress}%)"
                    )

                    # Get agent class
                    agent_class = AGENT_CLASSES.get(stage)
                    if not agent_class:
                        logger.warning(
                            f"Task {task_id}: No agent found for stage {stage}"
                        )
                        continue

                    # Create agent and execute
                    agent = agent_class(session)  # type: ignore[arg-type]

                    try:
                        result = await agent.execute(task_id, payload)

                        stage_elapsed = time.time() - stage_start
                        stage_times[stage] = stage_elapsed

                        logger.info(
                            f"Task {task_id}: [Stage {i}/{len(STAGE_ORDER)-1}] {stage} completed "
                            f"in {stage_elapsed:.2f}s"
                        )

                        # Merge result into payload for next stage
                        payload.update(result)

                    except TaskCancelledException:
                        # Task was cancelled
                        logger.info(f"Task {task_id}: Cancelled at stage {stage}")
                        await self._mark_cancelled(session, task_id)
                        return

                    except Exception as e:
                        # Stage failed
                        stage_elapsed = time.time() - stage_start
                        logger.error(
                            f"Task {task_id}: Stage {stage} failed after {stage_elapsed:.2f}s: {str(e)}",
                            exc_info=True,
                        )
                        await self._mark_failed(session, task_id, stage, str(e))
                        return

                # All stages completed
                total_elapsed = time.time() - task_start
                stage_summary = ", ".join(f"{s}={t:.2f}s" for s, t in stage_times.items())
                logger.info(
                    f"Task {task_id}: All stages completed successfully - "
                    f"total_time={total_elapsed:.2f}s ({stage_summary})"
                )
                await self._mark_completed(session, task_id)

            except Exception as e:
                # Task failed
                total_elapsed = time.time() - task_start
                logger.error(
                    f"Task {task_id}: Unexpected error after {total_elapsed:.2f}s: {str(e)}",
                    exc_info=True,
                )
                await self._mark_failed(session, task_id, "UNKNOWN", str(e))

            finally:
                TaskOrchestrator._cancelled_tasks.discard(task_id)
                TaskOrchestrator._deleted_tasks.discard(task_id)

    async def cancel_task(self, task_id: str):
        """
        Request task cancellation

        Args:
            task_id: Task ID to cancel
        """
        logger.info(f"Task {task_id}: Cancellation requested")
        TaskOrchestrator._cancelled_tasks.add(task_id)

    async def mark_task_deleted(self, task_id: str):
        """
        Mark a task as deleted (when force delete is used)

        Args:
            task_id: Task ID that was deleted
        """
        logger.info(f"Task {task_id}: Marked as deleted")
        TaskOrchestrator._deleted_tasks.add(task_id)
        TaskOrchestrator._cancelled_tasks.add(task_id)  # Also add to cancelled so processing stops

    async def _mark_cancelled(self, session: AsyncSession, task_id: str):
        """Mark task as cancelled"""
        from .database.connection import get_session_maker
        from .database.models import PrecheckTask
        from .services.task_service import TaskService

        # Use a fresh session in case the current one is in a broken state
        session_maker = get_session_maker()
        async with session_maker() as new_session:
            task_service = TaskService(new_session)
            await task_service.update_task_progress(
                task_id, "CANCELLED", 100, status="CANCELLED"
            )
            await task_service.log_event(task_id, "CANCELLED", "info", "Task was cancelled")

    async def _mark_failed(
        self, session: AsyncSession, task_id: str, stage: str, error: str
    ):
        """Mark task as failed"""
        from .database.connection import get_session_maker
        from .database.models import PrecheckTask
        from .services.task_service import TaskService

        # Use a fresh session in case the current one is in a broken state
        session_maker = get_session_maker()
        async with session_maker() as new_session:
            task_service = TaskService(new_session)
            await task_service.update_task_progress(
                task_id, stage, 0, status="FAILED", error_message=error
            )
            await task_service.log_event(
                task_id, stage, "error", f"Task failed at {stage}: {error}"
            )

    async def _mark_completed(self, session: AsyncSession, task_id: str):
        """Mark task as completed"""
        from .services.task_service import TaskService

        task_service = TaskService(session)
        await task_service.update_task_progress(
            task_id, "DONE", 100, status="COMPLETED"
        )
        await task_service.log_event(task_id, "DONE", "info", "Task completed successfully")

    def get_status(self) -> Dict[str, Any]:
        """
        Get orchestrator status

        Returns:
            Status dict with running tasks and capacity info
        """
        return {
            "max_concurrent": self.max_concurrent,
            "running_tasks": len(self.running_tasks),
            "available_slots": self.max_concurrent - len(self.running_tasks),
            "running_task_ids": list(self.running_tasks.keys()),
        }

    @classmethod
    def is_cancelled(cls, task_id: str) -> bool:
        """
        Check if a task is marked as cancelled (class method for global access)

        Args:
            task_id: Task ID to check

        Returns:
            True if task is cancelled, False otherwise
        """
        return task_id in cls._cancelled_tasks

    async def start_periodic_recovery(self):
        """Start periodic background task to recover stuck tasks"""
        if settings.task_startup_recovery:
            asyncio.create_task(self._periodic_recovery_loop())
            logger.info(
                f"Started periodic task recovery (interval: {settings.task_recovery_interval}s)"
            )

    async def _periodic_recovery_loop(self):
        """Periodically scan for and recover stuck tasks"""
        while True:
            try:
                await asyncio.sleep(settings.task_recovery_interval)
                # Call the module-level recover_stuck_tasks function, passing self as orchestrator
                recovered = await recover_stuck_tasks(self)
                if recovered > 0:
                    logger.info(f"Periodic recovery: recovered {recovered} stuck tasks")
            except asyncio.CancelledError:
                logger.info("Periodic recovery loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic recovery: {e}", exc_info=True)


async def recover_stuck_tasks(orchestrator: Optional[TaskOrchestrator] = None) -> int:
    """
    Scan for and recover stuck tasks on startup or periodically.

    A task is considered "stuck" if:
    - Status is QUEUED and updated_at is older than task_timeout

    Recovery logic:
    - If cancel_requested=True: Mark as CANCELLED
    - Otherwise: Mark as FAILED with timeout message

    Args:
        orchestrator: Optional orchestrator instance. If None, uses global instance.

    Returns:
        Number of tasks recovered (marked as cancelled or failed)
    """
    from .services.task_service import TaskService

    if orchestrator is None:
        orchestrator = get_orchestrator()

    session_maker = get_session_maker()
    recovered_count = 0
    now = datetime.now(timezone.utc)
    timeout_threshold = now - timedelta(seconds=settings.task_timeout)

    async with session_maker() as session:
        task_service = TaskService(session)

        # Find QUEUED tasks that haven't been updated recently
        query = select(PrecheckTask).where(
            PrecheckTask.status == "QUEUED",
            PrecheckTask.updated_at < timeout_threshold,
        )

        result = await session.execute(query)
        stuck_tasks = result.scalars().all()

        for task in stuck_tasks:
            try:
                logger.warning(
                    f"Found stuck task {task.id}: last updated {task.updated_at.isoformat()}, "
                    f"current stage {task.current_stage}, cancel_requested={task.cancel_requested}"
                )

                # If cancel was requested, mark as CANCELLED, otherwise FAILED
                if task.cancel_requested:
                    await task_service.update_task_progress(
                        task.id,
                        task.current_stage,
                        task.progress,
                        status="CANCELLED",
                    )
                    await task_service.log_event(
                        task.id,
                        "QUEUED",
                        "warning",
                        f"Task marked as CANCELLED (recovery - cancel was requested)",
                    )
                else:
                    await task_service.update_task_progress(
                        task.id,
                        task.current_stage,
                        task.progress,
                        status="FAILED",
                        error_message=f"Task timeout: no activity for {settings.task_timeout}s",
                    )
                    await task_service.log_event(
                        task.id,
                        "QUEUED",
                        "warning",
                        f"Task marked as failed due to timeout (recovery)",
                    )
                recovered_count += 1

            except Exception as e:
                logger.error(f"Failed to recover stuck task {task.id}: {e}", exc_info=True)

    if recovered_count > 0:
        logger.warning(f"Recovered {recovered_count} stuck tasks")

    return recovered_count


# Global orchestrator instance
_orchestrator: Optional[TaskOrchestrator] = None


def get_orchestrator() -> TaskOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TaskOrchestrator()
    return _orchestrator
