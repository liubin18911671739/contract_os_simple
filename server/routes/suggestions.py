"""
Suggestion API Routes
Endpoints for managing suggestions and risk level adjustments
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.connection import get_session_maker
from server.schemas.pydantic_models import (
    CreateSuggestionRequest,
    EvidenceChainResponse,
    RiskAdjustmentResponse,
    SuggestionResponse,
    SuggestionRevisionResponse,
    UpdateSuggestionRequest,
    AdjustRiskLevelRequest,
)
from server.services.suggestion_service import SuggestionService

router = APIRouter(prefix="/api/risks", tags=["suggestions"])


@router.get("/{risk_id}/suggestions", response_model=List[SuggestionResponse])
async def get_suggestions(risk_id: str):
    """
    Get all suggestions for a risk

    Args:
        risk_id: Risk ID

    Returns:
        List of suggestions with revision counts
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        service = SuggestionService(session)
        suggestions = await service.get_suggestions_for_risk(risk_id)
        return suggestions


@router.post("/{risk_id}/suggestions", status_code=status.HTTP_201_CREATED, response_model=SuggestionResponse)
async def create_suggestion(risk_id: str, request: CreateSuggestionRequest):
    """
    Create a new suggestion for a risk

    Args:
        risk_id: Risk ID
        request: Suggestion creation request

    Returns:
        Created suggestion
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        service = SuggestionService(session)
        suggestion_id = await service.create_suggestion(
            risk_id=risk_id,
            suggestion_text=request.suggestion_text,
            created_by="user",  # Could be from auth context in the future
        )

        # Get the created suggestion
        suggestions = await service.get_suggestions_for_risk(risk_id)
        for suggestion in suggestions:
            if suggestion["id"] == suggestion_id:
                return suggestion

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created suggestion",
        )


@router.put("/suggestions/{suggestion_id}", response_model=SuggestionRevisionResponse)
async def update_suggestion(suggestion_id: str, request: UpdateSuggestionRequest):
    """
    Update a suggestion (creates a new revision)

    Args:
        suggestion_id: Suggestion ID
        request: Update request

    Returns:
        The new revision record
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        service = SuggestionService(session)
        try:
            revision = await service.update_suggestion(
                suggestion_id=suggestion_id,
                new_text=request.suggestion_text,
                created_by="user",  # Could be from auth context
            )
            return {
                "id": revision.id,
                "suggestion_id": revision.suggestion_id,
                "revision_no": revision.revision_no,
                "suggestion_text": revision.suggestion_text,
                "created_by": revision.created_by,
                "created_at": revision.created_at.isoformat(),
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )


@router.get("/suggestions/{suggestion_id}/revisions", response_model=List[SuggestionRevisionResponse])
async def get_suggestion_revisions(suggestion_id: str):
    """
    Get revision history for a suggestion

    Args:
        suggestion_id: Suggestion ID

    Returns:
        List of all revisions ordered by revision number
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        service = SuggestionService(session)
        try:
            revisions = await service.get_suggestion_revisions(suggestion_id)
            return revisions
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )


@router.put("/{risk_id}/level", response_model=RiskAdjustmentResponse)
async def adjust_risk_level(risk_id: str, request: AdjustRiskLevelRequest):
    """
    Adjust the risk level for a risk

    Args:
        risk_id: Risk ID
        request: Adjustment request

    Returns:
        Updated risk information
    """
    # Validate risk level
    valid_levels = ["HIGH", "MEDIUM", "LOW", "INFO"]
    if request.risk_level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid risk level. Must be one of: {', '.join(valid_levels)}",
        )

    session_maker = get_session_maker()
    async with session_maker() as session:
        service = SuggestionService(session)
        try:
            result = await service.adjust_risk_level(
                risk_id=risk_id,
                new_level=request.risk_level,
                adjusted_by="user",  # Could be from auth context
                reason=request.reason,
            )
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )


@router.get("/{risk_id}/evidence-chain", response_model=EvidenceChainResponse)
async def get_evidence_chain(risk_id: str):
    """
    Get the complete evidence chain for a risk

    This includes:
    - Risk summary and level
    - Clause text
    - Rule hits
    - KB citations with document info
    - Evidences
    - Suggestions

    Args:
        risk_id: Risk ID

    Returns:
        Complete evidence chain
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        service = SuggestionService(session)
        try:
            chain = await service.get_evidence_chain(risk_id)
            return chain
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
