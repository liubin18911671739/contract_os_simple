"""
Split Agent - Split contract into clauses
"""

import re
import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Clause
from server.agents.base import BaseAgent


class SplitAgent(BaseAgent):
    """Split contract text into clauses"""

    stage_name = "STRUCTURING"

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Split contract text into clauses

        Args:
            task_id: Task ID
            payload: Dict with 'text' field from parse stage

        Returns:
            Dict with clause count
        """
        text = payload.get("text", "")

        if not text:
            raise ValueError("No text provided from parse stage")

        # Split into clauses
        clauses = self._split_text_into_clauses(text)

        # Save to database
        for i, clause_data in enumerate(clauses):
            clause_id = f"clause_{uuid.uuid4().hex[:12]}"

            clause = Clause(
                id=f"id_{uuid.uuid4().hex[:12]}",
                task_id=task_id,
                clause_id=clause_id,
                title=clause_data["title"],
                text=clause_data["text"],
                order_no=clause_data["order_no"],
            )

            self.session.add(clause)

        await self.session.commit()
        await self.update_progress(task_id, 25)

        await self.log_event(task_id, "info", f"Extracted {len(clauses)} clauses")

        return {"clause_count": len(clauses)}

    def _split_text_into_clauses(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into clauses using pattern matching

        Args:
            text: Contract text

        Returns:
            List of clause dicts with title, text, order_no
        """
        lines = text.split("\n")
        clauses = []
        current_clause = {"title": "", "text": "", "order_no": 0}

        # Pattern for clause headers
        header_pattern = re.compile(
            r"^(\d+\.|\d+\.\d+|[第]\d+[条条款章]|[A-Z][A-Z\s]+$|第[一二三四五六七八九十\d]+[条款章])"
        )

        for line in lines:
            stripped = line.strip()

            # Check if line looks like a header
            is_header = header_pattern.match(stripped)

            if is_header and current_clause["text"]:
                # Save current clause and start new one
                clauses.append(current_clause.copy())
                current_clause = {
                    "title": stripped,
                    "text": "",
                    "order_no": len(clauses),
                }
            else:
                if is_header:
                    current_clause["title"] = stripped
                    current_clause["order_no"] = len(clauses)
                current_clause["text"] += line + "\n"

        # Add last clause
        if current_clause["text"].strip():
            clauses.append(current_clause)

        # Fallback: if no clauses found, split by paragraphs
        if len(clauses) <= 1:
            clauses = []
            paragraphs = text.split("\n\n")
            for i, para in enumerate(paragraphs):
                if para.strip():
                    clauses.append(
                        {
                            "title": f"Clause {i + 1}",
                            "text": para.strip(),
                            "order_no": i,
                        }
                    )

        return clauses
