"""
Pydantic models for API request/response validation
Ensures API compatibility with the original Node.js version
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

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
    kb_collection_ids: List[str] = Field(
        ..., description="KB collection IDs to use"
    )
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

    total_tasks: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_contracts: int
    total_kb_collections: int
