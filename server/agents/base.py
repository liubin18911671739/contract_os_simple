"""
Base Agent class
All agents inherit from this and implement the execute method
"""
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import PrecheckTask
from ..services.task_service import TaskService


class BaseAgent(ABC):
    """Base class for all precheck agents"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_service = TaskService(session)

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Stage name for this agent"""
        pass

    @abstractmethod
    async def execute(
        self, task_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the agent's logic

        Args:
            task_id: Task ID
            payload: Data from previous stages

        Returns:
            Result data to pass to next stage
        """
        pass

    async def run(
        self, task_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the agent with logging and error handling

        Args:
            task_id: Task ID
            payload: Data from previous stages

        Returns:
            Result data
        """
        await self.log_event(task_id, "info", f"Starting {self.stage_name} stage")

        try:
            result = await self.execute(task_id, payload)

            await self.log_event(
                task_id,
                "info",
                f"Completed {self.stage_name} stage",
                meta=result,
            )

            return result

        except Exception as e:
            await self.log_event(
                task_id,
                "error",
                f"{self.stage_name} stage failed: {str(e)}",
            )
            raise

    async def log_event(
        self,
        task_id: str,
        level: str,
        message: str,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """Log a task event"""
        await self.task_service.log_event(task_id, self.stage_name, level, message, meta)

    async def check_cancelled(self, task_id: str) -> bool:
        """Check if task was cancelled"""
        return await self.task_service.is_cancel_requested(task_id)

    async def update_progress(self, task_id: str, progress: int):
        """Update task progress"""
        await self.task_service.update_task_progress(
            task_id, self.stage_name, progress
        )
