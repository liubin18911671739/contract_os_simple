"""
Suggestion Agent - Generate modification suggestions for risks using LLM
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
from sqlalchemy.orm import selectinload

from server.agents.base import BaseAgent, TaskCancelledException
from server.database.connection import fetch_all_sql
from server.database.models import (
    Clause,
    KBCitation,
    KBChunk,
    KBDocument,
    Risk,
    RuleHit,
    Suggestion,
)
from server.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class SuggestionAgent(BaseAgent):
    """Generate modification suggestions for each risk using LLM"""

    stage_name = "SUGGESTION"

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.llm_service = get_llm_service()

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate suggestions for all risks in the task

        Args:
            task_id: Task ID
            payload: Data from previous stages

        Returns:
            Dict with suggestion count
        """
        stage_start = time.time()

        # Get all risks for this task with their related data
        query = (
            select(Risk)
            .options(
                selectinload(Risk.clause),
                selectinload(Risk.kb_citations).selectinload(KBCitation.chunk).selectinload(KBChunk.document),
                selectinload(Risk.rule_hits),
            )
            .where(Risk.task_id == task_id)
        )
        result = await self.session.execute(query)
        risks = result.scalars().all()

        logger.info(
            f"Task {task_id}: Starting SUGGESTION stage for {len(risks)} risks"
        )

        # Batch collection: collect all suggestions before committing
        suggestions_batch = []
        total_risks = len(risks)
        progress_step = 7  # Progress range for this stage (75% to 82%)

        suggestion_count = 0
        risk_times = []

        for i, risk in enumerate(risks, 1):
            risk_start = time.time()
            logger.debug(
                f"Task {task_id}: [{i}/{total_risks}] Processing risk {risk.id}"
            )

            # Check for cancellation
            await self.check_cancelled(task_id)

            # Get clause text
            clause = risk.clause
            clause_text = clause.text if clause else ""

            # Get KB citations
            kb_citations = []
            for citation in risk.kb_citations:
                chunk_text = ""
                doc_title = ""
                doc_type = ""
                if citation.chunk:
                    chunk_text = citation.chunk.text
                    if citation.chunk.document:
                        doc_title = citation.chunk.document.title
                        doc_type = citation.chunk.document.doc_type

                kb_citations.append({
                    "quote_text": citation.quote_text,
                    "chunk_text": chunk_text,
                    "doc_title": doc_title,
                    "doc_type": doc_type,
                    "score": citation.score,
                })

            # Get rule hits
            rule_hits_data = []
            for hit in risk.rule_hits:
                rule_hits_data.append({
                    "rule_name": hit.rule_name,
                    "matched_text": hit.matched_text,
                    "meta": hit.meta_json,
                })

            # Build prompt
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(
                risk_summary=risk.summary,
                risk_level=risk.risk_level,
                risk_type=risk.risk_type,
                clause_text=clause_text,
                kb_citations=kb_citations,
                rule_hits=rule_hits_data,
            )

            try:
                # Call LLM with cancellation support
                response = await self._call_llm_with_cancellation(
                    task_id,
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )

                # Create suggestion from LLM response
                suggestion_data = response.get("suggestion", {})
                suggestion_text = suggestion_data.get("text", "")
                rationale = suggestion_data.get("rationale", "")
                legal_basis = suggestion_data.get("legal_basis", "")

                # If no suggestion text, generate a generic one
                if not suggestion_text:
                    suggestion_text = self._get_generic_suggestion(risk.risk_level, risk.risk_type)

                # Combine rationale and legal basis into the suggestion text if available
                full_suggestion = suggestion_text
                if rationale:
                    full_suggestion += f"\n\n理由：{rationale}"
                if legal_basis:
                    full_suggestion += f"\n\n法律依据：{legal_basis}"

                # Create suggestion record
                suggestion_id = f"sug_{uuid.uuid4().hex[:12]}"
                suggestion = Suggestion(
                    id=suggestion_id,
                    risk_id=risk.id,
                    suggestion_text=full_suggestion.strip(),
                    created_by="ai",  # Mark as AI-generated
                )
                suggestions_batch.append(suggestion)
                suggestion_count += 1

                risk_elapsed = time.time() - risk_start
                risk_times.append(risk_elapsed)

                logger.debug(
                    f"Task {task_id}: [{i}/{total_risks}] Generated suggestion, "
                    f"time={risk_elapsed:.2f}s"
                )

            except Exception as e:
                # Create generic suggestion when LLM fails
                logger.error(
                    f"Task {task_id}: [{i}/{total_risks}] LLM suggestion generation failed: {str(e)}",
                    exc_info=True,
                )
                # Fallback to generic suggestion
                suggestion_id = f"sug_{uuid.uuid4().hex[:12]}"
                suggestion = Suggestion(
                    id=suggestion_id,
                    risk_id=risk.id,
                    suggestion_text=self._get_generic_suggestion(risk.risk_level, risk.risk_type),
                    created_by="ai_fallback",
                )
                suggestions_batch.append(suggestion)
                suggestion_count += 1

            # Update progress after each risk
            current_progress = 75 + int(progress_step * i / total_risks)
            await self.update_progress(task_id, current_progress)

        # Single batch commit for all suggestions
        if suggestions_batch:
            self.session.add_all(suggestions_batch)
            logger.debug(
                f"Task {task_id}: Batch adding {len(suggestions_batch)} suggestions to database"
            )

        # Single commit for all changes
        await self.session.commit()

        stage_elapsed = time.time() - stage_start
        avg_risk_time = sum(risk_times) / len(risk_times) if risk_times else 0

        logger.info(
            f"Task {task_id}: SUGGESTION completed - "
            f"suggestions={suggestion_count}, "
            f"total_time={stage_elapsed:.2f}s, avg_risk={avg_risk_time:.2f}s"
        )

        await self.update_progress(task_id, 82)
        await self.log_event(task_id, "info", f"Created {suggestion_count} suggestions")

        return {"suggestion_count": suggestion_count}

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
        """Get system prompt for suggestion generation (Chinese)"""
        return """你是一位专业的法律顾问，负责为合同风险提供具体的修改建议。

你的任务是：
1. 分析风险的具体问题
2. 提供清晰、可执行的修改建议
3. 说明修改的理由和依据
4. 引用相关法律条款或政策依据（从知识库引用中提取）

请使用以下JSON格式回复：
{
  "suggestion": {
    "text": "具体的修改建议文本，应该可以直接用于修改合同",
    "rationale": "修改的理由和依据",
    "legal_basis": "相关法律条款或政策依据"
  }
}

注意事项：
- 建议应该具体明确，能够直接用于修改合同
- 理由应该简明扼要，突出关键点
- 法律依据应从提供的知识库引用中提取
- 如果风险等级为HIGH，建议应更加详细和重要
- 建议应该使用专业的法律术语，但保持易懂"""

    def _build_user_prompt(
        self,
        risk_summary: str,
        risk_level: str,
        risk_type: str,
        clause_text: str,
        kb_citations: List[Dict],
        rule_hits: List[Dict],
    ) -> str:
        """Build user prompt with risk context (Chinese)"""
        # Limit clause length
        MAX_CLAUSE_LENGTH = 2000
        if len(clause_text) > MAX_CLAUSE_LENGTH:
            clause_text = clause_text[:MAX_CLAUSE_LENGTH] + "..."

        prompt = f"""请为以下合同风险提供修改建议：

风险等级：{risk_level}
风险类型：{risk_type}
风险摘要：{risk_summary}

条款内容：
{clause_text}
"""

        # Add KB citations
        if kb_citations:
            prompt += "\n相关知识库引用：\n"
            for citation in kb_citations[:4]:  # Maximum 4 citations
                doc_info = f"【{citation.get('doc_title', 'KB')}】"
                prompt += f"\n{doc_info} {citation.get('quote_text', '')[:200]}...\n"

        # Add rule hits
        if rule_hits:
            prompt += "\n匹配的规则：\n"
            for hit in rule_hits:
                prompt += f"\n- {hit.get('rule_name', '')}: {hit.get('matched_text', '')[:100]}...\n"

        prompt += "\n请按指定JSON格式提供修改建议。"

        return prompt

    def _get_generic_suggestion(self, risk_level: str, risk_type: str) -> str:
        """Generate a generic suggestion when LLM fails"""
        level_actions = {
            "HIGH": "强烈建议修改此条款以降低法律风险",
            "MEDIUM": "建议对此条款进行审查和适当修改",
            "LOW": "建议关注此条款，可考虑优化",
            "INFO": "此为信息性提示，可根据实际情况决定是否修改",
        }

        type_specific = {
            "LIABILITY": "责任条款应明确双方的责任范围和赔偿限额",
            "TERMINATION": "终止条款应公平合理，避免单方面权利",
            "PAYMENT": "付款条款应明确金额、时间和方式",
            "CONFIDENTIALITY": "保密条款应明确保密范围和期限",
            "IP": "知识产权条款应明确归属和使用权限",
            "DISPUTE": "争议解决条款应选择合适的争议解决方式",
            "COMPLIANCE": "应确保条款符合相关法律法规要求",
            "GENERAL": "建议对此条款进行审查以确保合法合规",
        }

        action = level_actions.get(risk_level, "建议审查此条款")
        specific = type_specific.get(risk_type, "")

        if specific:
            return f"{action}。\n\n{specific}。"

        return action
