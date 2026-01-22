"""
Task Orchestrator
Manages the 8-stage task processing pipeline
Replaces BullMQ with asyncio
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database.connection import get_session_maker
from .agents.parse_agent import ParseAgent
from .agents.split_agent import SplitAgent
from .agents.stub_agents import (
    RulesAgent,
    KBRetrievalAgent,
    EvidenceAgent,
    QCAgent,
)
from .agents.llm_risk_agent import LLMRiskAgent
from .agents.report_agent import ReportAgent


# Configure logging
logger = logging.getLogger(__name__)

# Task stages in order
STAGE_ORDER = [
    "QUEUED",
    "PARSING",  # 12%
    "STRUCTURING",  # 25%
    "RULE_SCORING",  # 37%
    "KB_RETRIEVAL",  # 50%
    "LLM_RISK",  # 75%
    "EVIDENCING",  # 87%
    "QCING",  # 95%
    "DONE",  # 100%
]

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

    def __init__(self, max_concurrent_tasks: int = None):
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.cancelled_tasks: set[str] = set()
        # Semaphore for limiting concurrent tasks
        self.max_concurrent = max_concurrent_tasks or settings.max_concurrent_tasks
        self.task_semaphore = asyncio.Semaphore(self.max_concurrent)
        logger.info(f"TaskOrchestrator initialized with max_concurrent={self.max_concurrent}")

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
                logger.info(f"Task {task_id} started (active: {len(self.running_tasks)}/{self.max_concurrent})")
                try:
                    await self._process_task(task_id)
                finally:
                    logger.info(f"Task {task_id} completed")

        task = asyncio.create_task(_run_with_semaphore())
        self.running_tasks[task_id] = task

        # Cleanup when done
        def cleanup(t):
            self.running_tasks.pop(task_id, None)
            logger.debug(f"Task {task_id} cleaned up from running tasks")

        task.add_done_callback(cleanup)

    async def _process_task(self, task_id: str):
        """
        Internal method to process task through stages

        Args:
            task_id: Task ID
        """
        session_maker = get_session_maker()

        async with session_maker() as session:
            payload: Dict[str, Any] = {}

            try:
                logger.info(f"Task {task_id}: Starting processing through {len(STAGE_ORDER) - 1} stages")

                # Process each stage
                for i, stage in enumerate(STAGE_ORDER[1:], 1):  # Skip QUEUED
                    # Check if cancelled
                    if task_id in self.cancelled_tasks:
                        logger.info(f"Task {task_id}: Cancel requested at stage {stage}")
                        await self._mark_cancelled(session, task_id)
                        return

                    # Get agent class
                    agent_class = AGENT_CLASSES.get(stage)
                    if not agent_class:
                        logger.warning(f"Task {task_id}: No agent found for stage {stage}")
                        continue

                    # Create agent and execute
                    logger.info(f"Task {task_id}: Starting stage {i}/{len(STAGE_ORDER)-1} - {stage}")
                    agent = agent_class(session)

                    try:
                        result = await agent.execute(task_id, payload)
                        logger.info(f"Task {task_id}: Completed stage {stage} successfully")

                        # Merge result into payload for next stage
                        payload.update(result)

                    except Exception as e:
                        # Stage failed
                        logger.error(f"Task {task_id}: Stage {stage} failed with error: {str(e)}")
                        await self._mark_failed(session, task_id, stage, str(e))
                        return

                # All stages completed
                logger.info(f"Task {task_id}: All stages completed successfully")
                await self._mark_completed(session, task_id)

            except Exception as e:
                # Task failed
                logger.error(f"Task {task_id}: Unexpected error: {str(e)}", exc_info=True)
                await self._mark_failed(session, task_id, "UNKNOWN", str(e))

            finally:
                self.cancelled_tasks.discard(task_id)

    async def cancel_task(self, task_id: str):
        """
        Request task cancellation

        Args:
            task_id: Task ID to cancel
        """
        logger.info(f"Task {task_id}: Cancellation requested")
        self.cancelled_tasks.add(task_id)

    async def _mark_cancelled(self, session: AsyncSession, task_id: str):
        """Mark task as cancelled"""
        from .database.models import PrecheckTask
        from .services.task_service import TaskService

        task_service = TaskService(session)
        await task_service.update_task_progress(
            task_id, "CANCELLED", 100, status="CANCELLED"
        )
        await task_service.log_event(
            task_id, "info", "Task was cancelled"
        )

    async def _mark_failed(
        self, session: AsyncSession, task_id: str, stage: str, error: str
    ):
        """Mark task as failed"""
        from .database.models import PrecheckTask
        from .services.task_service import TaskService

        task_service = TaskService(session)
        await task_service.update_task_progress(
            task_id, stage, 0, status="FAILED", error_message=error
        )
        await task_service.log_event(
            task_id, "error", f"Task failed at {stage}: {error}"
        )

    async def _mark_completed(self, session: AsyncSession, task_id: str):
        """Mark task as completed"""
        from .services.task_service import TaskService

        task_service = TaskService(session)
        await task_service.update_task_progress(
            task_id, "DONE", 100, status="COMPLETED"
        )
        await task_service.log_event(
            task_id, "info", "Task completed successfully"
        )

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


# Global orchestrator instance
_orchestrator: Optional[TaskOrchestrator] = None


def get_orchestrator() -> TaskOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TaskOrchestrator()
    return _orchestrator
