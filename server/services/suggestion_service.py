"""
Suggestion Service
Manages suggestion CRUD operations and risk level adjustments
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from server.database.models import (
    Clause,
    Evidence,
    KBCitation,
    KBChunk,
    KBDocument,
    Risk,
    RuleHit,
    Suggestion,
    SuggestionRevision,
)


class SuggestionService:
    """Service for suggestion and risk level management"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_suggestion(
        self,
        risk_id: str,
        suggestion_text: str,
        created_by: Optional[str] = None,
    ) -> str:
        """
        Create a new suggestion for a risk

        Args:
            risk_id: Risk ID
            suggestion_text: Suggestion text
            created_by: Optional creator identifier

        Returns:
            Suggestion ID
        """
        suggestion_id = f"sug_{uuid.uuid4().hex[:12]}"
        suggestion = Suggestion(
            id=suggestion_id,
            risk_id=risk_id,
            suggestion_text=suggestion_text,
            created_by=created_by,
        )
        self.session.add(suggestion)
        await self.session.commit()

        return suggestion_id

    async def update_suggestion(
        self,
        suggestion_id: str,
        new_text: str,
        created_by: Optional[str] = None,
    ) -> SuggestionRevision:
        """
        Update a suggestion and create a revision record

        Args:
            suggestion_id: Suggestion ID
            new_text: New suggestion text
            created_by: Optional creator identifier

        Returns:
            The new revision record
        """
        # Get current suggestion
        result = await self.session.execute(
            select(Suggestion).where(Suggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()

        if not suggestion:
            raise ValueError(f"Suggestion {suggestion_id} not found")

        # Get current revision count
        revision_result = await self.session.execute(
            select(SuggestionRevision)
            .where(SuggestionRevision.suggestion_id == suggestion_id)
            .order_by(SuggestionRevision.revision_no.desc())
        )
        current_revisions = revision_result.scalars().all()
        next_revision_no = (len(current_revisions) + 1) if current_revisions else 1

        # Update suggestion text
        suggestion.suggestion_text = new_text

        # Create revision record
        revision_id = f"rev_{uuid.uuid4().hex[:12]}"
        revision = SuggestionRevision(
            id=revision_id,
            suggestion_id=suggestion_id,
            revision_no=next_revision_no,
            suggestion_text=new_text,
            created_by=created_by,
        )
        self.session.add(revision)

        await self.session.commit()

        # Refresh to get updated data
        await self.session.refresh(revision)

        return revision

    async def get_suggestions_for_risk(self, risk_id: str) -> List[Dict[str, Any]]:
        """
        Get all suggestions for a risk with revision counts

        Args:
            risk_id: Risk ID

        Returns:
            List of suggestion dicts
        """
        result = await self.session.execute(
            select(Suggestion).where(Suggestion.risk_id == risk_id)
        )
        suggestions = result.scalars().all()

        # Get revision counts for each suggestion
        suggestion_list = []
        for suggestion in suggestions:
            revision_result = await self.session.execute(
                select(SuggestionRevision)
                .where(SuggestionRevision.suggestion_id == suggestion.id)
            )
            revisions = revision_result.scalars().all()

            suggestion_list.append({
                "id": suggestion.id,
                "risk_id": suggestion.risk_id,
                "suggestion_text": suggestion.suggestion_text,
                "created_by": suggestion.created_by,
                "created_at": suggestion.created_at.isoformat(),
                "revision_count": len(revisions),
            })

        return suggestion_list

    async def get_suggestion_revisions(
        self, suggestion_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get revision history for a suggestion

        Args:
            suggestion_id: Suggestion ID

        Returns:
            List of revision dicts
        """
        result = await self.session.execute(
            select(SuggestionRevision)
            .where(SuggestionRevision.suggestion_id == suggestion_id)
            .order_by(SuggestionRevision.revision_no)
        )
        revisions = result.scalars().all()

        return [
            {
                "id": rev.id,
                "suggestion_id": rev.suggestion_id,
                "revision_no": rev.revision_no,
                "suggestion_text": rev.suggestion_text,
                "created_by": rev.created_by,
                "created_at": rev.created_at.isoformat(),
            }
            for rev in revisions
        ]

    async def adjust_risk_level(
        self,
        risk_id: str,
        new_level: str,
        adjusted_by: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adjust the risk level for a risk

        Args:
            risk_id: Risk ID
            new_level: New risk level (HIGH/MEDIUM/LOW/INFO)
            adjusted_by: Optional identifier of who made the adjustment
            reason: Optional reason for the adjustment

        Returns:
            Updated risk dict
        """
        # Get risk
        result = await self.session.execute(
            select(Risk).where(Risk.id == risk_id)
        )
        risk = result.scalar_one_or_none()

        if not risk:
            raise ValueError(f"Risk {risk_id} not found")

        # Store original level if not already stored
        if not risk.qc_flags_json.get("original_risk_level"):
            risk.qc_flags_json["original_risk_level"] = risk.risk_level

        # Update risk level
        risk.risk_level = new_level
        risk.qc_flags_json["adjusted_at"] = datetime.now(timezone.utc).isoformat()
        if adjusted_by:
            risk.qc_flags_json["adjusted_by"] = adjusted_by
        if reason:
            risk.qc_flags_json["adjustment_reason"] = reason

        await self.session.commit()
        await self.session.refresh(risk)

        return {
            "id": risk.id,
            "risk_level": risk.risk_level,
            "original_risk_level": risk.qc_flags_json.get("original_risk_level"),
            "adjusted_at": risk.qc_flags_json.get("adjusted_at"),
            "adjusted_by": risk.qc_flags_json.get("adjusted_by"),
            "adjustment_reason": risk.qc_flags_json.get("adjustment_reason"),
        }

    async def get_evidence_chain(self, risk_id: str) -> Dict[str, Any]:
        """
        Get the complete evidence chain for a risk

        Args:
            risk_id: Risk ID

        Returns:
            Evidence chain dict with all related data
        """
        # Get risk with clause
        result = await self.session.execute(
            select(Risk)
            .options(selectinload(Risk.clause))
            .where(Risk.id == risk_id)
        )
        risk = result.scalar_one_or_none()

        if not risk:
            raise ValueError(f"Risk {risk_id} not found")

        clause = risk.clause
        clause_data = None
        if clause:
            clause_data = {
                "id": clause.id,
                "clause_id": clause.clause_id,
                "title": clause.title,
                "text": clause.text,
                "page_ref": clause.page_ref,
                "order_no": clause.order_no,
            }

        # Get rule hits
        rule_hits_result = await self.session.execute(
            select(RuleHit)
            .where(RuleHit.risk_id == risk_id)
        )
        rule_hits = [
            {
                "id": hit.id,
                "rule_id": hit.rule_id,
                "rule_name": hit.rule_name,
                "matched_text": hit.matched_text,
                "meta": hit.meta_json,
            }
            for hit in rule_hits_result.scalars().all()
        ]

        # Get KB citations with chunk and document info
        kb_citations_result = await self.session.execute(
            select(KBCitation)
            .options(
                selectinload(KBCitation.chunk).selectinload(
                    KBChunk.document
                )
            )
            .where(KBCitation.risk_id == risk_id)
        )
        kb_citations = []
        for citation in kb_citations_result.scalars().all():
            chunk_data = None
            doc_data = None
            if citation.chunk:
                chunk_data = {
                    "id": citation.chunk.id,
                    "chunk_no": citation.chunk.chunk_no,
                    "text": citation.chunk.text,
                }
                if citation.chunk.document:
                    doc_data = {
                        "id": citation.chunk.document.id,
                        "title": citation.chunk.document.title,
                        "doc_type": citation.chunk.document.doc_type,
                    }

            kb_citations.append({
                "id": citation.id,
                "chunk_id": citation.chunk_id,
                "score": citation.score,
                "quote_text": citation.quote_text,
                "doc_version": citation.doc_version,
                "chunk": chunk_data,
                "document": doc_data,
            })

        # Get evidences
        evidences_result = await self.session.execute(
            select(Evidence).where(Evidence.risk_id == risk_id)
        )
        evidences = [
            {
                "id": ev.id,
                "source_type": ev.source_type,
                "quote_text": ev.quote_text,
                "start_offset": ev.start_offset,
                "end_offset": ev.end_offset,
                "page_ref": ev.page_ref,
                "chunk_id": ev.chunk_id,
            }
            for ev in evidences_result.scalars().all()
        ]

        # Get suggestions
        suggestions = await self.get_suggestions_for_risk(risk_id)

        return {
            "risk_id": risk.id,
            "task_id": risk.task_id,
            "risk_summary": risk.summary,
            "risk_level": risk.risk_level,
            "original_risk_level": risk.qc_flags_json.get("original_risk_level"),
            "risk_type": risk.risk_type,
            "confidence": risk.confidence,
            "status": risk.status,
            "clause": clause_data,
            "rule_hits": rule_hits,
            "kb_citations": kb_citations,
            "evidences": evidences,
            "suggestions": suggestions,
            "adjusted_at": risk.qc_flags_json.get("adjusted_at"),
            "adjusted_by": risk.qc_flags_json.get("adjusted_by"),
            "adjustment_reason": risk.qc_flags_json.get("adjustment_reason"),
        }
