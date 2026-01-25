"""
LLM Risk Agent - Analyze risks using LLM with batch commits
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.agents.base import BaseAgent, TaskCancelledException
from server.database.connection import fetch_all_sql
from server.database.models import Clause, KBCitation, Risk
from server.services.kb_service import KBService
from server.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class LLMRiskAgent(BaseAgent):
    """Analyze clause risks using LLM with batch commits for better concurrency"""

    stage_name = "LLM_RISK"

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.llm_service = get_llm_service()

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze risks for each clause using LLM with batch commits

        Args:
            task_id: Task ID
            payload: Data from previous stages

        Returns:
            Dict with risk count
        """
        stage_start = time.time()

        # Get all clauses for this task
        query = (
            select(Clause).where(Clause.task_id == task_id).order_by(Clause.order_no)
        )
        result = await self.session.execute(query)
        clauses = result.scalars().all()

        logger.info(
            f"Task {task_id}: Starting LLM_RISK stage for {len(clauses)} clauses"
        )

        # Batch collection: collect all risks and citations before committing
        risks_batch = []
        citations_batch = []
        total_clauses = len(clauses)
        progress_step = 25  # Progress range for this stage (50% to 75%)

        risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0, "ERROR": 0}
        clause_times = []

        for i, clause in enumerate(clauses, 1):
            clause_start = time.time()
            logger.debug(
                f"Task {task_id}: [{i}/{total_clauses}] Processing clause {clause.clause_id}"
            )
            # Check for cancellation (will raise TaskCancelledException if cancelled)
            await self.check_cancelled(task_id)

            # Get KB hits for this clause
            kb_hits = await fetch_all_sql(
                """
                SELECT chunk_id, quote_text, doc_title, doc_version
                FROM kb_hits_temp
                WHERE task_id = ? AND clause_id = ?
                ORDER BY score ASC
                LIMIT 6
                """,
                (task_id, clause.id),  # Use clause.id (PK), not clause.clause_id
            )

            logger.debug(
                f"Task {task_id}: [{i}/{total_clauses}] {len(kb_hits)} KB hits available"
            )

            # Build prompt
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(clause.text, kb_hits)

            try:
                # Call LLM with cancellation support
                response = await self._call_llm_with_cancellation(
                    task_id,
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )

                # Parse risks
                risks = response.get("risks", [])

                # Create a mapping of valid chunk_ids from KB hits for validation
                valid_chunk_ids = {hit.get("chunk_id"): hit for hit in kb_hits}

                for risk_data in risks:
                    risk_level = risk_data.get("risk_level", "INFO")
                    risk_id = f"risk_{uuid.uuid4().hex[:12]}"

                    risk = Risk(
                        id=risk_id,
                        task_id=task_id,
                        clause_id=clause.id,  # Use clause.id (PK), not clause.clause_id
                        risk_level=risk_level,
                        risk_type=risk_data.get("risk_type", "GENERAL"),
                        confidence=risk_data.get("confidence", 0.5),
                        summary=risk_data.get("summary", ""),
                        status="NEEDS_REVIEW",
                    )

                    risks_batch.append(risk)

                    # Track risk counts
                    if risk_level in risk_counts:
                        risk_counts[risk_level] += 1

                    # Add KB citations - only use valid chunk_ids from KB hits
                    for kb_evidence in risk_data.get("kb_evidence", []):
                        # Try to match the LLM's chunk_id to a valid one, or use the first available
                        llm_chunk_id = kb_evidence.get("chunk_id", "")
                        quote_text = kb_evidence.get("quote_text", "")

                        # Find matching chunk by quote text or use first available
                        matched_chunk_id = None
                        if llm_chunk_id in valid_chunk_ids:
                            matched_chunk_id = llm_chunk_id
                        else:
                            # Try to find a chunk with matching quote text
                            for chunk_id, hit in valid_chunk_ids.items():
                                if quote_text and hit.get("quote_text", "") in quote_text:
                                    matched_chunk_id = chunk_id
                                    break
                                elif quote_text in hit.get("quote_text", ""):
                                    matched_chunk_id = chunk_id
                                    break

                            # If no match, use the first available chunk_id (or None if no KB hits)
                            if not matched_chunk_id and valid_chunk_ids:
                                matched_chunk_id = next(iter(valid_chunk_ids))

                        # Only create citation if we have a valid chunk_id
                        if matched_chunk_id:
                            citation_id = f"cit_{uuid.uuid4().hex[:12]}"
                            citation = KBCitation(
                                id=citation_id,
                                risk_id=risk_id,
                                chunk_id=matched_chunk_id,
                                score=0.8,
                                quote_text=quote_text or valid_chunk_ids[matched_chunk_id].get("quote_text", ""),
                                doc_version=kb_evidence.get("doc_version", 1),
                            )
                            citations_batch.append(citation)

                clause_elapsed = time.time() - clause_start
                clause_times.append(clause_elapsed)

                logger.debug(
                    f"Task {task_id}: [{i}/{total_clauses}] {len(risks)} risks, "
                    f"time={clause_elapsed:.2f}s"
                )

            except Exception as e:
                # Create NEEDS_REVIEW risk when LLM fails
                logger.error(
                    f"Task {task_id}: [{i}/{total_clauses}] LLM analysis failed: {str(e)}",
                    exc_info=True,
                )
                risk_id = f"risk_{uuid.uuid4().hex[:12]}"
                risk = Risk(
                    id=risk_id,
                    task_id=task_id,
                    clause_id=clause.id,  # Use clause.id (PK), not clause.clause_id
                    risk_level="INFO",
                    risk_type="LLM_ERROR",
                    confidence=0.0,
                    summary=f"AI分析失败: {str(e)}",
                    status="NEEDS_REVIEW",
                    qc_flags_json={
                        "llm_error": True,
                        "error_message": str(e),
                        "fallback_mode": "manual_review_required",
                        "error_timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                risks_batch.append(risk)
                risk_counts["ERROR"] += 1

            # Update progress after each clause to prevent timeout
            current_progress = 50 + int(progress_step * i / total_clauses)
            await self.update_progress(task_id, current_progress)

        # Single batch commit for all risks and citations
        if risks_batch:
            self.session.add_all(risks_batch)
            logger.debug(
                f"Task {task_id}: Batch adding {len(risks_batch)} risks to database"
            )

        if citations_batch:
            self.session.add_all(citations_batch)
            logger.debug(
                f"Task {task_id}: Batch adding {len(citations_batch)} KB citations to database"
            )

        # Single commit for all changes
        await self.session.commit()

        stage_elapsed = time.time() - stage_start
        avg_clause_time = sum(clause_times) / len(clause_times) if clause_times else 0

        logger.info(
            f"Task {task_id}: LLM_RISK completed - "
            f"risks={len(risks_batch)} (HIGH={risk_counts['HIGH']}, "
            f"MEDIUM={risk_counts['MEDIUM']}, LOW={risk_counts['LOW']}, "
            f"INFO={risk_counts['INFO']}, ERROR={risk_counts['ERROR']}), "
            f"total_time={stage_elapsed:.2f}s, avg_clause={avg_clause_time:.2f}s"
        )

        await self.update_progress(task_id, 75)

        await self.log_event(task_id, "info", f"Created {len(risks_batch)} risks")

        return {"risk_count": len(risks_batch)}

    async def _call_llm_with_cancellation(
        self,
        task_id: str,
        messages: List[Dict[str, str]],
        check_interval: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Call LLM with periodic cancellation checking

        This wraps the LLM call to allow cancellation during long-running API requests.

        Args:
            task_id: Task ID to check for cancellation
            messages: Messages to send to LLM
            check_interval: How often to check for cancellation (seconds)

        Returns:
            LLM response dict

        Raises:
            TaskCancelledException: If task is cancelled during LLM call
        """
        # Create a task for the LLM call
        llm_task = asyncio.create_task(
            self.llm_service.chat_with_json(messages, temperature=0.3)
        )

        try:
            # Monitor task for cancellation
            while not llm_task.done():
                try:
                    # Wait a bit then check cancellation
                    await asyncio.wait_for(
                        asyncio.shield(llm_task), timeout=check_interval
                    )
                    break  # LLM call completed
                except asyncio.TimeoutError:
                    # Check if cancelled
                    await self.check_cancelled(task_id)
                    # Continue waiting
        except TaskCancelledException:
            # Cancel the LLM task if still running
            if not llm_task.done():
                llm_task.cancel()
            raise

        # Get result
        return await llm_task

    def _get_system_prompt(self) -> str:
        """Get system prompt for risk analysis (Chinese)"""
        return """你是一位专业的法律合同风险分析专家。请基于中国法律框架分析合同条款并识别潜在风险。

风险等级: HIGH（高）, MEDIUM（中）, LOW（低）, INFO（信息）

常见风险类型:
- LIABILITY: 责任与赔偿条款问题
- TERMINATION: 不公平的终止条款
- PAYMENT: 付款条款与违约金
- CONFIDENTIALITY: 数据保护与保密义务
- IP: 知识产权相关问题
- DISPUTE: 争议解决机制
- COMPLIANCE: 法律合规性
- GENERAL: 其他一般风险

请使用以下JSON格式回复:
{
  "risks": [
    {
      "risk_level": "HIGH|MEDIUM|LOW|INFO",
      "risk_type": "类型",
      "confidence": 0.0-1.0,
      "summary": "风险摘要（中文）",
      "kb_evidence": [
        {
          "chunk_id": "id",
          "quote_text": "知识库相关文本",
          "doc_version": 1
        }
      ]
    }
  ]
}"""

    def _build_user_prompt(self, clause_text: str, kb_hits: List[Dict]) -> str:
        """Build user prompt with clause and KB context (Chinese, with length limits)"""
        # Limit clause length to prevent context overflow
        MAX_CLAUSE_LENGTH = 3000
        if len(clause_text) > MAX_CLAUSE_LENGTH:
            clause_text = clause_text[:MAX_CLAUSE_LENGTH] + "..."

        prompt = f"""请分析以下合同条款的法律风险：

条款内容：
{clause_text}
"""

        # Limit KB references count and length
        if kb_hits:
            prompt += "\n相关知识库引用：\n"
            for hit in kb_hits[:4]:  # Maximum 4 KB references
                quote = hit.get('quote_text', '')[:300]  # Max 300 chars per quote
                prompt += f"\n- {hit.get('doc_title', 'KB')}: {quote}...\n"

        prompt += "\n请按指定JSON格式提供风险分析结果。"

        # Log warning if prompt is too long
        total_chars = len(prompt)
        if total_chars > 50000:
            logger.warning(f"Prompt length {total_chars} chars, consider truncating")

        return prompt
