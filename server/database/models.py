"""
SQLAlchemy ORM models for Contract OS Simple
Based on the original PostgreSQL schema
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (JSON, Boolean, CheckConstraint, DateTime, Float,
                        ForeignKey, Index, Integer, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .connection import Base

# ==================== Contracts ====================


class Contract(Base):
    """Contracts table"""

    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    contract_name: Mapped[str] = mapped_column(String, nullable=False)
    counterparty: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contract_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    versions: Mapped[list["ContractVersion"]] = relationship(
        "ContractVersion", back_populates="contract", cascade="all, delete-orphan"
    )


class ContractVersion(Base):
    """Contract versions table"""

    __tablename__ = "contract_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    contract_id: Mapped[str] = mapped_column(
        String, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    object_key: Mapped[str] = mapped_column(String, nullable=False)
    sha256: Mapped[str] = mapped_column(String, nullable=False)
    mime: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    contract: Mapped["Contract"] = relationship("Contract", back_populates="versions")
    precheck_tasks: Mapped[list["PrecheckTask"]] = relationship(
        "PrecheckTask", back_populates="contract_version"
    )


# ==================== Tasks ====================


class ConfigSnapshot(Base):
    """Configuration snapshots for reproducibility"""

    __tablename__ = "config_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ruleset_version: Mapped[str] = mapped_column(String, nullable=False)
    model_config_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    prompt_template_version: Mapped[str] = mapped_column(String, nullable=False)
    kb_collection_versions_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    precheck_tasks: Mapped[list["PrecheckTask"]] = relationship(
        "PrecheckTask", back_populates="config_snapshot"
    )


class PrecheckTask(Base):
    """Precheck tasks table"""

    __tablename__ = "precheck_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    contract_version_id: Mapped[str] = mapped_column(
        String, ForeignKey("contract_versions.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="QUEUED",
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[str] = mapped_column(String, default="QUEUED")
    config_snapshot_id: Mapped[str] = mapped_column(
        String, ForeignKey("config_snapshots.id"), nullable=False
    )
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    kb_mode: Mapped[str] = mapped_column(String, nullable=False)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint("kb_mode IN ('STRICT', 'RELAXED')", name="check_kb_mode"),
        Index("idx_precheck_tasks_status", "status"),
        Index("idx_precheck_tasks_status_created", "status", "created_at"),
        Index("idx_precheck_tasks_status_updated", "status", "updated_at"),
    )

    # Relationships
    contract_version: Mapped["ContractVersion"] = relationship(
        "ContractVersion", back_populates="precheck_tasks"
    )
    config_snapshot: Mapped["ConfigSnapshot"] = relationship(
        "ConfigSnapshot", back_populates="precheck_tasks"
    )
    events: Mapped[list["TaskEvent"]] = relationship(
        "TaskEvent", back_populates="task", cascade="all, delete-orphan"
    )
    kb_snapshots: Mapped[list["TaskKBSnapshot"]] = relationship(
        "TaskKBSnapshot", back_populates="task", cascade="all, delete-orphan"
    )
    clauses: Mapped[list["Clause"]] = relationship(
        "Clause", back_populates="task", cascade="all, delete-orphan"
    )
    risks: Mapped[list["Risk"]] = relationship(
        "Risk", back_populates="task", cascade="all, delete-orphan"
    )
    kb_hits_temp: Mapped[list["KBHitTemp"]] = relationship(
        "KBHitTemp", back_populates="task", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="task", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="task", cascade="all, delete-orphan"
    )


class TaskEvent(Base):
    """Task events table"""

    __tablename__ = "task_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String, ForeignKey("precheck_tasks.id", ondelete="CASCADE"), nullable=False
    )
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "level IN ('info', 'warning', 'error')", name="check_event_level"
        ),
        Index("idx_task_events_task_id", "task_id", "ts"),
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    task: Mapped["PrecheckTask"] = relationship("PrecheckTask", back_populates="events")


class TaskKBSnapshot(Base):
    """Task KB snapshots for versioning"""

    __tablename__ = "task_kb_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String, ForeignKey("precheck_tasks.id", ondelete="CASCADE"), nullable=False
    )
    collection_id: Mapped[str] = mapped_column(String, nullable=False)
    collection_version: Mapped[int] = mapped_column(Integer, nullable=False)
    frozen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_task_kb_snapshots_task_collection",
            "task_id",
            "collection_id",
            unique=True,
        ),
    )

    # Relationships
    task: Mapped["PrecheckTask"] = relationship(
        "PrecheckTask", back_populates="kb_snapshots"
    )


# ==================== Clauses and Risks ====================


class Clause(Base):
    """Clauses table"""

    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String, ForeignKey("precheck_tasks.id", ondelete="CASCADE"), nullable=False
    )
    clause_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_clauses_task_id", "task_id"),
        Index("idx_clauses_task_clause", "task_id", "clause_id", unique=True),
    )

    # Relationships
    task: Mapped["PrecheckTask"] = relationship(
        "PrecheckTask", back_populates="clauses"
    )
    risks: Mapped[list["Risk"]] = relationship(
        "Risk", back_populates="clause", cascade="all, delete-orphan"
    )
    kb_hits_temp: Mapped[list["KBHitTemp"]] = relationship(
        "KBHitTemp", back_populates="clause"
    )


class Risk(Base):
    """Risks table"""

    __tablename__ = "risks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String, ForeignKey("precheck_tasks.id", ondelete="CASCADE"), nullable=False
    )
    clause_id: Mapped[str] = mapped_column(
        String, ForeignKey("clauses.id"), nullable=False
    )
    risk_level: Mapped[str] = mapped_column(String, nullable=False)

    risk_type: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="NEEDS_REVIEW",
    )

    __table_args__: tuple[CheckConstraint, CheckConstraint, CheckConstraint, Index, Index, Index, Index] = (
        CheckConstraint(
            "risk_level IN ('HIGH', 'MEDIUM', 'LOW', 'INFO')",
            name="check_risk_level",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="check_confidence"),
        CheckConstraint(
            "status IN ('NEEDS_REVIEW', 'CONFIRMED', 'DISMISSED')",
            name="check_risk_status",
        ),
        Index("idx_risks_task_id", "task_id"),
        Index("idx_risks_clause_id", "clause_id"),
        Index("idx_risks_risk_level", "risk_level"),
        Index("idx_risks_status", "status"),
    )

    qc_flags_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    task: Mapped["PrecheckTask"] = relationship("PrecheckTask", back_populates="risks")
    clause: Mapped["Clause"] = relationship("Clause", back_populates="risks")
    rule_hits: Mapped[list["RuleHit"]] = relationship(
        "RuleHit", back_populates="risk", cascade="all, delete-orphan"
    )
    evidences: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="risk", cascade="all, delete-orphan"
    )
    kb_citations: Mapped[list["KBCitation"]] = relationship(
        "KBCitation", back_populates="risk", cascade="all, delete-orphan"
    )
    suggestions: Mapped[list["Suggestion"]] = relationship(
        "Suggestion", back_populates="risk", cascade="all, delete-orphan"
    )


class RuleHit(Base):
    """Rule hits table"""

    __tablename__ = "rule_hits"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    risk_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("risks.id", ondelete="CASCADE"), nullable=True
    )
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    rule_name: Mapped[str] = mapped_column(String, nullable=False)
    matched_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    risk: Mapped["Risk"] = relationship("Risk", back_populates="rule_hits")


class Evidence(Base):
    """Evidence table"""

    __tablename__ = "evidences"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    risk_id: Mapped[str] = mapped_column(
        String, ForeignKey("risks.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('CONTRACT', 'KB')", name="check_evidence_source"
        ),
        Index("idx_evidences_risk_id", "risk_id"),
    )

    quote_text: Mapped[str] = mapped_column(Text, nullable=False)
    start_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    chunk_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    risk: Mapped["Risk"] = relationship("Risk", back_populates="evidences")


# ==================== Knowledge Base ====================


class KBCollection(Base):
    """KB collections table"""

    __tablename__ = "kb_collections"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    scope: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "scope IN ('GLOBAL', 'TENANT', 'PROJECT', 'DEPT')",
            name="check_kb_scope",
        ),
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    documents: Mapped[list["KBDocument"]] = relationship(
        "KBDocument", back_populates="collection", cascade="all, delete-orphan"
    )


class KBDocument(Base):
    """KB documents table"""

    __tablename__ = "kb_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    collection_id: Mapped[str] = mapped_column(
        String, ForeignKey("kb_collections.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    doc_type: Mapped[str] = mapped_column(String, nullable=False)
    object_key: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_kb_documents_collection_id", "collection_id"),)

    # Relationships
    collection: Mapped["KBCollection"] = relationship(
        "KBCollection", back_populates="documents"
    )
    chunks: Mapped[list["KBChunk"]] = relationship(
        "KBChunk", back_populates="document", cascade="all, delete-orphan"
    )


class KBChunk(Base):
    """KB chunks table"""

    __tablename__ = "kb_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_no: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("idx_kb_chunks_document_id", "document_id"),
        Index("idx_kb_chunks_doc_chunk", "document_id", "chunk_no", unique=True),
    )

    # Relationships
    document: Mapped["KBDocument"] = relationship("KBDocument", back_populates="chunks")
    kb_citations: Mapped[list["KBCitation"]] = relationship(
        "KBCitation", back_populates="chunk"
    )
    kb_hits_temp: Mapped[list["KBHitTemp"]] = relationship(
        "KBHitTemp", back_populates="chunk"
    )


class KBEmbedding(Base):
    """KB embeddings table - stored separately for Faiss"""

    __tablename__ = "kb_embeddings"

    chunk_id: Mapped[str] = mapped_column(
        String, ForeignKey("kb_chunks.id", ondelete="CASCADE"), primary_key=True
    )
    # Note: Actual embedding vector is stored in Faiss index, not here
    # This table just tracks which chunks have been embedded


class KBCitation(Base):
    """KB citations table"""

    __tablename__ = "kb_citations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    risk_id: Mapped[str] = mapped_column(
        String, ForeignKey("risks.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[str] = mapped_column(
        String, ForeignKey("kb_chunks.id", ondelete="SET NULL"), nullable=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    quote_text: Mapped[str] = mapped_column(Text, nullable=False)
    doc_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_kb_citations_risk_id", "risk_id"),
        Index("idx_kb_citations_chunk_id", "chunk_id"),
    )

    # Relationships
    risk: Mapped["Risk"] = relationship("Risk", back_populates="kb_citations")
    chunk: Mapped["KBChunk"] = relationship("KBChunk", back_populates="kb_citations")


class KBHitTemp(Base):
    """Temporary table for KB retrieval results"""

    __tablename__ = "kb_hits_temp"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String, ForeignKey("precheck_tasks.id", ondelete="CASCADE"), nullable=False
    )
    clause_id: Mapped[str] = mapped_column(
        String, ForeignKey("clauses.id"), nullable=False
    )
    chunk_id: Mapped[str] = mapped_column(
        String, ForeignKey("kb_chunks.id", ondelete="SET NULL"), nullable=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    quote_text: Mapped[str] = mapped_column(Text, nullable=False)
    doc_title: Mapped[str] = mapped_column(String, nullable=False)
    doc_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_kb_hits_temp_task_clause", "task_id", "clause_id"),)

    # Relationships
    task: Mapped["PrecheckTask"] = relationship(
        "PrecheckTask", back_populates="kb_hits_temp"
    )
    clause: Mapped["Clause"] = relationship("Clause", back_populates="kb_hits_temp")
    chunk: Mapped["KBChunk"] = relationship("KBChunk", back_populates="kb_hits_temp")


# ==================== Review and Audit ====================


class Suggestion(Base):
    """Suggestions table"""

    __tablename__ = "suggestions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    risk_id: Mapped[str] = mapped_column(
        String, ForeignKey("risks.id", ondelete="CASCADE"), nullable=False
    )
    suggestion_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    risk: Mapped["Risk"] = relationship("Risk", back_populates="suggestions")
    revisions: Mapped[list["SuggestionRevision"]] = relationship(
        "SuggestionRevision", back_populates="suggestion", cascade="all, delete-orphan"
    )


class SuggestionRevision(Base):
    """Suggestion revisions table"""

    __tablename__ = "suggestion_revisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    suggestion_id: Mapped[str] = mapped_column(
        String, ForeignKey("suggestions.id", ondelete="CASCADE"), nullable=False
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    suggestion_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_suggestion_revisions_suggestion_rev",
            "suggestion_id",
            "revision_no",
            unique=True,
        ),
    )

    # Relationships
    suggestion: Mapped["Suggestion"] = relationship(
        "Suggestion", back_populates="revisions"
    )


class Review(Base):
    """Reviews table"""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String, ForeignKey("precheck_tasks.id", ondelete="CASCADE"), nullable=False
    )
    conclusion: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "conclusion IN ('APPROVE', 'MODIFY', 'ESCALATE')",
            name="check_review_conclusion",
        ),
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    task: Mapped["PrecheckTask"] = relationship(
        "PrecheckTask", back_populates="reviews"
    )


class Report(Base):
    """Reports table"""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String, ForeignKey("precheck_tasks.id", ondelete="CASCADE"), nullable=False
    )
    object_key: Mapped[str] = mapped_column(String, nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    task: Mapped["PrecheckTask"] = relationship(
        "PrecheckTask", back_populates="reports"
    )


class AuditLog(Base):
    """Audit logs table"""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    object_type: Mapped[str] = mapped_column(String, nullable=False)
    object_id: Mapped[str] = mapped_column(String, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (Index("idx_audit_logs_object", "object_type", "object_id"),)
