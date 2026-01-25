"""
Pydantic models for API request/response validation
Ensures API compatibility with the original Node.js version
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== Contract Models ====================


class CreateContractRequest(BaseModel):
    """Request to create a contract"""

    contract_name: str = Field(..., description="Contract name")
    counterparty: Optional[str] = Field(None, description="Counterparty name")
    contract_type: Optional[str] = Field(None, description="Contract type")


class ContractResponse(BaseModel):
    """Contract response"""

    id: str
    contract_name: str
    counterparty: Optional[str]
    contract_type: Optional[str]
    created_at: str
    versions: List[Dict[str, Any]]


# ==================== Task Models ====================


class CreatePrecheckTaskRequest(BaseModel):
    """Request to create a precheck task"""

    contract_version_id: str = Field(..., description="Contract version ID")
    kb_collection_ids: List[str] = Field(..., description="KB collection IDs to use")
    kb_mode: str = Field("STRICT", description="KB mode: STRICT or RELAXED")
    template_id: Optional[str] = Field(None, description="Report template ID")


class TaskResponse(BaseModel):
    """Task response"""

    id: str
    contract_name: Optional[str]
    status: str
    progress: int
    current_stage: str
    error_message: Optional[str]
    cancel_requested: bool
    kb_mode: str
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    """Task list response"""

    tasks: List[TaskResponse]
    total: int
    page: int
    limit: int


class TaskEventResponse(BaseModel):
    """Task event response"""

    id: str
    ts: str
    stage: str
    level: str
    message: str
    meta: Dict[str, Any]


class TaskSummaryResponse(BaseModel):
    """Task summary response"""

    clause_count: int
    high_risks: int
    medium_risks: int
    low_risks: int
    info_risks: int


class ClauseResponse(BaseModel):
    """Clause with risk response"""

    id: str
    clause_id: str
    title: Optional[str]
    text: str
    order_no: int
    risk_id: Optional[str]
    risk_level: Optional[str]
    risk_summary: Optional[str]
    risk_status: Optional[str]


# ==================== KB Models ====================


class CreateKBCollectionRequest(BaseModel):
    """Request to create KB collection"""

    name: str = Field(..., description="Collection name")
    scope: str = Field("GLOBAL", description="Collection scope")


class KBCollectionResponse(BaseModel):
    """KB collection response"""

    id: str
    name: str
    scope: str
    version: int
    is_enabled: bool
    document_count: Optional[int] = 0
    created_at: str


class ImportKBDocumentRequest(BaseModel):
    """Request to import KB document"""

    title: str = Field(..., description="Document title")
    doc_type: str = Field(..., description="Document type")
    file_path: str = Field(..., description="Path to document file")


# ==================== Review Models ====================


class SetConclusionRequest(BaseModel):
    """Request to set task conclusion"""

    conclusion: str = Field(..., description="APPROVE, MODIFY, or ESCALATE")
    notes: Optional[str] = Field(None, description="Review notes")


class GenerateReportRequest(BaseModel):
    """Request to generate report"""

    format: str = Field("html", description="Report format (html, pdf)")


# ==================== Common Models ====================


class ErrorResponse(BaseModel):
    """Error response"""

    error: str


class SuccessResponse(BaseModel):
    """Simple success response"""

    success: bool
    id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    timestamp: str


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response"""

    total_contracts: int
    high_risk_findings: int
    compliance_rate: int
    avg_processing_time: float
    trends_7d: "TrendsData"


class TrendsData(BaseModel):
    """7-day trend data"""

    contracts_analyzed: int
    risk_discovery: int
    compliance_rate: int


class RecentTaskResponse(BaseModel):
    """Recent task for dashboard"""

    id: str
    contract_name: str
    status: str
    progress: int
    created_at: str
    high_risks: int
    medium_risks: int


class RecentTasksResponse(BaseModel):
    """Recent tasks list response"""

    tasks: List[RecentTaskResponse]
    total: int
    page: int
    limit: int


# ==================== Metrics Models ====================


class MetricsOverviewResponse(BaseModel):
    """Metrics overview response"""

    period: dict[str, str]
    total_tasks: int
    completion_rate: float
    avg_duration_seconds: float
    risk_distribution: dict[str, int]
    daily_breakdown: List[dict[str, Any]]


class F1ScoreResponse(BaseModel):
    """F1 score response"""

    f1_score: float
    precision: float
    recall: float


class HallucinationRateResponse(BaseModel):
    """Hallucination rate response"""

    rate: float
    trend: float


class BaselineComparisonResponse(BaseModel):
    """Baseline comparison response - compare current period with baseline"""

    # F1 Score metrics
    current_f1: float
    baseline_f1: float
    f1_change: float  # percentage change

    # Precision metrics
    current_precision: float
    baseline_precision: float
    precision_change: float

    # Recall metrics
    current_recall: float
    baseline_recall: float
    recall_change: float

    # Hallucination metrics
    current_hallucination: float
    baseline_hallucination: float
    hallucination_change: float

    # Period info
    current_period: dict[str, str]
    baseline_period: dict[str, str]


class RiskLevelStats(BaseModel):
    """Statistics for a single risk level"""

    total: int
    confirmed: int
    dismissed: int
    pending: int
    confirmation_rate: float
    accuracy_rate: float


class RiskAssessmentResponse(BaseModel):
    """Detailed risk assessment response"""

    by_level: dict[str, RiskLevelStats]
    by_type: dict[str, int]  # risk_type -> count
    overall_confirmation_rate: float
    overall_accuracy: float
    period: dict[str, str]


# ==================== KB Document Models ====================


class KBDocumentResponse(BaseModel):
    """KB document response"""

    id: str
    collection_id: str
    title: str
    doc_type: str
    chunk_count: int
    indexed_count: int
    status: str
    created_at: str


class KBSearchRequest(BaseModel):
    """Request to search knowledge base"""

    query: str = Field(..., description="Search query text", min_length=1)
    collection_ids: List[str] = Field(default_factory=list, description="Collection IDs to search (empty = all)")
    top_k: int = Field(6, ge=1, le=20, description="Number of results to return")


class KBSearchResultResponse(BaseModel):
    """KB search result response"""

    chunk_id: str
    text: str = Field(..., description="Matching text snippet")
    score: float = Field(..., description="Similarity score (0-1)")
    doc_title: str
    doc_version: int
    doc_id: Optional[str] = None
    collection_id: Optional[str] = None


class KBChunkResponse(BaseModel):
    """KB chunk response"""

    id: str
    document_id: str
    chunk_index: int
    text: str
    is_indexed: bool
    created_at: str


class KBCollectionStatsResponse(BaseModel):
    """KB collection statistics response"""

    id: str
    name: str
    document_count: int
    chunk_count: int
    indexed_count: int
    avg_chunk_size: float
    total_storage_mb: float


# ==================== Suggestion Models ====================


class SuggestionResponse(BaseModel):
    """Suggestion response"""

    id: str
    risk_id: str
    suggestion_text: str
    created_by: Optional[str]
    created_at: str
    revision_count: int


class CreateSuggestionRequest(BaseModel):
    """Request to create a suggestion"""

    suggestion_text: str = Field(..., description="Suggestion text")


class UpdateSuggestionRequest(BaseModel):
    """Request to update a suggestion"""

    suggestion_text: str = Field(..., description="Updated suggestion text")


class SuggestionRevisionResponse(BaseModel):
    """Suggestion revision response"""

    id: str
    suggestion_id: str
    revision_no: int
    suggestion_text: str
    created_by: Optional[str]
    created_at: str


class AdjustRiskLevelRequest(BaseModel):
    """Request to adjust risk level"""

    risk_level: str = Field(..., description="New risk level: HIGH, MEDIUM, LOW, or INFO")
    reason: Optional[str] = Field(None, description="Reason for adjustment")


class RiskAdjustmentResponse(BaseModel):
    """Risk adjustment response"""

    id: str
    risk_level: str
    original_risk_level: Optional[str]
    adjusted_at: Optional[str]
    adjusted_by: Optional[str]
    adjustment_reason: Optional[str]


class RuleHitInChain(BaseModel):
    """Rule hit in evidence chain"""

    id: str
    rule_id: str
    rule_name: str
    matched_text: str
    meta: Dict[str, Any]


class KBCitationInChain(BaseModel):
    """KB citation in evidence chain"""

    id: str
    chunk_id: Optional[str]
    score: float
    quote_text: str
    doc_version: int
    chunk: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None


class EvidenceInChain(BaseModel):
    """Evidence in evidence chain"""

    id: str
    source_type: str
    quote_text: str
    start_offset: Optional[int]
    end_offset: Optional[int]
    page_ref: Optional[str]
    chunk_id: Optional[str]


class ClauseInChain(BaseModel):
    """Clause in evidence chain"""

    id: str
    clause_id: str
    title: Optional[str]
    text: str
    page_ref: Optional[str]
    order_no: int


class EvidenceChainResponse(BaseModel):
    """Complete evidence chain response"""

    risk_id: str
    task_id: str
    risk_summary: str
    risk_level: str
    original_risk_level: Optional[str]
    risk_type: str
    confidence: float
    status: str
    clause: Optional[ClauseInChain]
    rule_hits: List[RuleHitInChain]
    kb_citations: List[KBCitationInChain]
    evidences: List[EvidenceInChain]
    suggestions: List[SuggestionResponse]
    adjusted_at: Optional[str]
    adjusted_by: Optional[str]
    adjustment_reason: Optional[str]
