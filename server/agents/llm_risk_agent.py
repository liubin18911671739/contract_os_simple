"""
LLM Risk Agent - Analyze risks using LLM
"""

import json
import logging
import uuid
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.connection import fetch_all_sql
from server.database.models import Clause, KBCitation, Risk
from server.services.kb_service import KBService
from server.services.llm_service import get_llm_service
from server.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class LLMRiskAgent(BaseAgent):
    """Analyze clause risks using LLM"""

    stage_name = "LLM_RISK"

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.llm_service = get_llm_service()

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze risks for each clause using LLM

        Args:
            task_id: Task ID
            payload: Data from previous stages

        Returns:
            Dict with risk count
        """
        # Get all clauses for this task
        query = (
            select(Clause).where(Clause.task_id == task_id).order_by(Clause.order_no)
        )
        result = await self.session.execute(query)
        clauses = result.scalars().all()

        logger.info(
            f"Task {task_id}: Starting LLM risk analysis for {len(clauses)} clauses"
        )
        risks_created = []

        for i, clause in enumerate(clauses, 1):
            logger.debug(
                f"Task {task_id}: Processing clause {i}/{len(clauses)} - {clause.clause_id}"
            )
            # Check for cancellation
            if await self.check_cancelled(task_id):
                break

            # Get KB hits for this clause
            kb_hits = await fetch_all_sql(
                """
                SELECT chunk_id, quote_text, doc_title, doc_version
                FROM kb_hits_temp
                WHERE task_id = ? AND clause_id = ?
                ORDER BY score ASC
                LIMIT 6
                """,
                (task_id, clause.clause_id),
            )

            logger.debug(
                f"Task {task_id}: Clause {i}/{len(clauses)} - {len(kb_hits)} KB hits found"
            )

            # Build prompt
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(clause.text, kb_hits)

            try:
                # Call LLM
                response = await self.llm_service.chat_with_json(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                )

                # Parse risks
                risks = response.get("risks", [])
                logger.debug(
                    f"Task {task_id}: Clause {i}/{len(clauses)} - {len(risks)} risks identified"
                )

                for risk_data in risks:
                    risk_id = f"risk_{uuid.uuid4().hex[:12]}"

                    risk = Risk(
                        id=risk_id,
                        task_id=task_id,
                        clause_id=clause.clause_id,
                        risk_level=risk_data.get("risk_level", "INFO"),
                        risk_type=risk_data.get("risk_type", "GENERAL"),
                        confidence=risk_data.get("confidence", 0.5),
                        summary=risk_data.get("summary", ""),
                        status="NEEDS_REVIEW",
                    )

                    self.session.add(risk)
                    risks_created.append(risk_id)

                    # Add KB citations
                    for kb_evidence in risk_data.get("kb_evidence", []):
                        citation_id = f"cit_{uuid.uuid4().hex[:12]}"
                        citation = KBCitation(
                            id=citation_id,
                            risk_id=risk_id,
                            chunk_id=kb_evidence.get("chunk_id", ""),
                            score=0.8,
                            quote_text=kb_evidence.get("quote_text", ""),
                            doc_version=kb_evidence.get("doc_version", 1),
                        )
                        self.session.add(citation)

                await self.session.commit()
                logger.debug(
                    f"Task {task_id}: Clause {i}/{len(clauses)} - {len(risks)} risks saved to database"
                )

            except Exception as e:
                # Create NEEDS_REVIEW risk when LLM fails
                logger.error(
                    f"Task {task_id}: Clause {i}/{len(clauses)} - LLM analysis failed: {str(e)}",
                    exc_info=True,
                )
                risk_id = f"risk_{uuid.uuid4().hex[:12]}"
                risk = Risk(
                    id=risk_id,
                    task_id=task_id,
                    clause_id=clause.clause_id,
                    risk_level="INFO",
                    risk_type="LLM_ERROR",
                    confidence=0.0,
                    summary=f"LLM analysis failed: {str(e)}",
                    status="NEEDS_REVIEW",
                    qc_flags_json={"llm_error": True, "error_message": str(e)},
                )

                self.session.add(risk)
                await self.session.commit()
                risks_created.append(risk_id)
                logger.info(
                    f"Task {task_id}: Clause {i}/{len(clauses)} - Created NEEDS_REVIEW risk for LLM error"
                )

        logger.info(
            f"Task {task_id}: LLM risk analysis completed - {len(risks_created)} risks created"
        )
        await self.update_progress(task_id, 75)

        await self.log_event(task_id, "info", f"Created {len(risks_created)} risks")

        return {"risk_count": len(risks_created)}

    def _get_system_prompt(self) -> str:
        """Get system prompt for risk analysis"""
        return """You are a legal contract risk analysis expert. Analyze contract clauses and identify potential risks.

Risk levels: HIGH, MEDIUM, LOW, INFO

Common risk types:
- LIABILITY: Liability and indemnification issues
- TERMINATION: Unfair termination clauses
- PAYMENT: Payment terms and penalties
- CONFIDENTIALITY: Data protection and confidentiality
- IP: Intellectual property issues
- DISPUTE: Dispute resolution concerns
- COMPLIANCE: Regulatory compliance
- GENERAL: Other general risks

Respond with JSON in this format:
{
  "risks": [
    {
      "risk_level": "HIGH|MEDIUM|LOW|INFO",
      "risk_type": "TYPE",
      "confidence": 0.0-1.0,
      "summary": "Clear description of the risk",
      "kb_evidence": [
        {
          "chunk_id": "id",
          "quote_text": "relevant text from KB",
          "doc_version": 1
        }
      ]
    }
  ]
}"""

    def _build_user_prompt(self, clause_text: str, kb_hits: List[Dict]) -> str:
        """Build user prompt with clause and KB context"""
        prompt = f"""Analyze this contract clause for legal risks:

Clause:
{clause_text}
"""

        if kb_hits:
            prompt += "\nRelevant knowledge base references:\n"
            for hit in kb_hits[:6]:
                prompt += f"\n- {hit.get('doc_title', 'KB')}: {hit.get('quote_text', '')[:200]}...\n"

        prompt += "\nProvide risk analysis in the specified JSON format."

        return prompt
