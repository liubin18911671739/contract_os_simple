"""
Stub Agents for remaining stages
These can be expanded later with full implementations
"""

import uuid
from typing import Any, Dict, List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.connection import fetch_one_sql
from server.database.models import (Clause, Evidence, KBHitTemp, Review,
                                     Risk, RuleHit)
from server.services.kb_service import KBService
from server.services.llm_service import get_llm_service
from server.agents.base import BaseAgent


class RulesAgent(BaseAgent):
    """Rule-based risk detection using keywords and patterns"""

    stage_name = "RULE_SCORING"

    # Define rules (can be loaded from database later)
    RULES = [
        {
            "rule_id": "unlimited_liability",
            "rule_name": "Unlimited Liability",
            "keywords": [
                "unlimited liability",
                "without limitation",
                "all liabilities",
            ],
            "risk_level": "HIGH",
            "risk_type": "LIABILITY",
        },
        {
            "rule_id": "auto_renewal",
            "rule_name": "Auto-Renewal Clause",
            "keywords": ["automatically renew", "auto-renew", "renew automatically"],
            "risk_level": "MEDIUM",
            "risk_type": "TERMINATION",
        },
        {
            "rule_id": "penalty_clause",
            "rule_name": "Penalty Clause",
            "keywords": ["penalty", "liquidated damages", "fine"],
            "risk_level": "MEDIUM",
            "risk_type": "PAYMENT",
        },
    ]

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rule-based risk detection"""
        query = select(Clause).where(Clause.task_id == task_id)
        result = await self.session.execute(query)
        clauses = result.scalars().all()

        rule_hits_count = 0

        for clause in clauses:
            clause_text_lower = clause.text.lower()

            for rule in self.RULES:
                # Check if any keyword matches
                if any(kw in clause_text_lower for kw in rule["keywords"]):
                    # Find matched text
                    matched_text = self._find_matched_text(
                        clause.text, rule["keywords"]
                    )

                    hit_id = f"rule_hit_{uuid.uuid4().hex[:12]}"
                    hit = RuleHit(
                        id=hit_id,
                        risk_id=None,  # Will be linked in LLM stage
                        rule_id=rule["rule_id"],
                        rule_name=rule["rule_name"],
                        matched_text=matched_text,
                        meta_json={
                            "risk_level": rule["risk_level"],
                            "risk_type": rule["risk_type"],
                        },
                    )

                    self.session.add(hit)
                    rule_hits_count += 1

        await self.session.commit()
        await self.update_progress(task_id, 37)

        await self.log_event(task_id, "info", f"Found {rule_hits_count} rule hits")

        return {"rule_hits_count": rule_hits_count}

    def _find_matched_text(self, text: str, keywords: List[str]) -> str:
        """Find text segment containing keyword"""
        for keyword in keywords:
            if keyword.lower() in text.lower():
                idx = text.lower().find(keyword.lower())
                start = max(0, idx - 50)
                end = min(len(text), idx + len(keyword) + 50)
                return "..." + text[start:end] + "..."
        return ""


class KBRetrievalAgent(BaseAgent):
    """Retrieve relevant KB documents for each clause"""

    stage_name = "KB_RETRIEVAL"

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.kb_service = KBService(session)

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve KB documents for each clause"""
        # Get KB collections for this task
        from server.services.task_service import TaskService

        task_service = TaskService(self.session)
        collection_ids = await task_service.get_task_kb_collections(task_id)

        # Get clauses
        query = select(Clause).where(Clause.task_id == task_id)
        result = await self.session.execute(query)
        clauses = result.scalars().all()

        kb_hits_count = 0

        for clause in clauses:
            for collection_id in collection_ids:
                # Search KB
                chunks = await self.kb_service.search_chunks(
                    collection_id, clause.text, top_k=10
                )

                # Rerank
                if chunks:
                    chunks = await self.kb_service.rerank_chunks(
                        clause.text, chunks, top_n=6
                    )

                # Store hits
                for chunk in chunks:
                    hit_id = f"kb_hit_{uuid.uuid4().hex[:12]}"
                    hit = KBHitTemp(
                        id=hit_id,
                        task_id=task_id,
                        clause_id=clause.clause_id,
                        chunk_id=chunk["chunk_id"],
                        score=chunk.get("_rerank_score", chunk["score"]),
                        quote_text=chunk["text"][:500],
                        doc_title=chunk.get("meta", {}).get("title", "KB Document"),
                        doc_version=1,
                    )

                    self.session.add(hit)
                    kb_hits_count += 1

        await self.session.commit()
        await self.update_progress(task_id, 50)

        await self.log_event(
            task_id, "info", f"Retrieved {kb_hits_count} KB references"
        )

        return {"kb_hits_count": kb_hits_count}


class EvidenceAgent(BaseAgent):
    """Collect evidence chain for risks"""

    stage_name = "EVIDENCING"

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Collect evidence for risks"""
        # Get all risks with their associated clauses in a single query
        # This fixes the N+1 query problem
        query = (
            select(Risk, Clause)
            .select_from(Risk)
            .join(Clause, Risk.clause_id == Clause.clause_id)
            .where(Risk.task_id == task_id)
        )
        result = await self.session.execute(query)
        risk_clause_pairs = result.all()

        evidence_count = 0

        for risk, clause in risk_clause_pairs:
            # Add contract evidence
            contract_evidence = Evidence(
                id=f"ev_{uuid.uuid4().hex[:12]}",
                risk_id=risk.id,
                source_type="CONTRACT",
                quote_text=clause.text[:500],
                page_ref=clause.page_ref,
            )

            self.session.add(contract_evidence)
            evidence_count += 1

        await self.session.commit()
        await self.update_progress(task_id, 87)

        await self.log_event(task_id, "info", f"Collected {evidence_count} evidences")

        return {"evidence_count": evidence_count}


class QCAgent(BaseAgent):
    """Quality Control agent"""

    stage_name = "QCING"

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform QC checks"""
        # Get task summary
        summary = await fetch_one_sql(
            """
            SELECT
                COUNT(DISTINCT c.id) as clause_count,
                COUNT(r.id) as risk_count,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'HIGH') as high_risk_count
            FROM precheck_tasks pt
            LEFT JOIN clauses c ON c.task_id = pt.id
            LEFT JOIN risks r ON r.task_id = pt.id
            WHERE pt.id = ?
            GROUP BY pt.id
            """,
            (task_id,),
        )

        qc_passed = True
        qc_flags = {}

        if summary:
            # Check QC criteria
            if summary.get("risk_count", 0) == 0:
                qc_passed = False
                qc_flags["no_risks"] = True

            if summary.get("high_risk_count", 0) > 5:
                qc_flags["many_high_risks"] = True

        # Store QC flags in task (optional)

        await self.update_progress(task_id, 95)

        await self.log_event(
            task_id,
            "info" if qc_passed else "warning",
            f"QC {'passed' if qc_passed else 'warning'}",
            meta=qc_flags,
        )

        return {"qc_passed": qc_passed, "qc_flags": qc_flags}


# ReportAgent has been moved to report_agent.py
