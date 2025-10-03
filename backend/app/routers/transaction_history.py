"""
Enhanced Transaction History Router for Story 2.5
Advanced transaction history with filtering, search, export, and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import get_db
from ..models import User
from ..schemas import ApiResponse
from ..services.transaction_history_service import transaction_history_service
from ..dependencies import require_authentication, rate_limit

router = APIRouter()


@router.get("/history", response_model=Dict[str, Any])
async def get_enhanced_transaction_history(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    # Filter parameters
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    status: Optional[str] = Query(None, description="Transaction status"),
    currency_type: Optional[str] = Query(None, description="Currency type"),
    transaction_type: Optional[str] = Query(None, description="Transaction type"),
    direction: Optional[str] = Query(None, description="Direction (sent/received)"),
    # Search and sorting
    search: Optional[str] = Query(None, description="Search query"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    # Pagination
    limit: int = Query(25, description="Number of transactions to return"),
    offset: int = Query(0, description="Number of transactions to skip"),
    _rate_limit: bool = Depends(rate_limit(max_requests=60, window_seconds=60))
):
    """
    Get enhanced transaction history with advanced filtering and search
    """
    try:
        # Build filters dictionary
        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if min_amount is not None:
            filters["min_amount"] = min_amount
        if max_amount is not None:
            filters["max_amount"] = max_amount
        if status:
            filters["status"] = status
        if currency_type:
            filters["currency_type"] = currency_type
        if transaction_type:
            filters["transaction_type"] = transaction_type
        if direction:
            filters["direction"] = direction
        
        # Validate sort parameters
        if sort_by not in ["created_at", "amount", "status"]:
            sort_by = "created_at"
        if sort_order not in ["asc", "desc"]:
            sort_order = "desc"
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        result = await transaction_history_service.get_enhanced_transaction_history(
            current_user, db, filters, search, sort_by, sort_order, limit, offset
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction history"
        )


@router.get("/search", response_model=Dict[str, Any])
async def search_transactions(
    q: str = Query(..., description="Search query"),
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    limit: int = Query(25, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Search transactions by hash, description, or other fields
    """
    try:
        if len(q.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters"
            )
        
        result = await transaction_history_service.get_enhanced_transaction_history(
            current_user, db, None, q.strip(), "created_at", "desc", limit, offset
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search transactions"
        )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_transaction_analytics(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    period: str = Query("30d", description="Analytics period (7d, 30d, 90d, 1y)"),
    _rate_limit: bool = Depends(rate_limit(max_requests=20, window_seconds=60))
):
    """
    Get transaction analytics and insights
    """
    try:
        if period not in ["7d", "30d", "90d", "1y"]:
            period = "30d"
        
        analytics = await transaction_history_service.get_transaction_analytics(
            current_user, db, period
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics"
        )


@router.post("/export", response_model=Dict[str, Any])
async def export_transactions(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    export_format: str = Query("csv", description="Export format (csv, pdf)"),
    # Filter parameters (same as history endpoint)
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    status: Optional[str] = Query(None, description="Transaction status"),
    currency_type: Optional[str] = Query(None, description="Currency type"),
    transaction_type: Optional[str] = Query(None, description="Transaction type"),
    direction: Optional[str] = Query(None, description="Direction (sent/received)"),
    search: Optional[str] = Query(None, description="Search query"),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Export transactions to CSV or PDF
    """
    try:
        if export_format not in ["csv", "pdf"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Export format must be 'csv' or 'pdf'"
            )
        
        # Build filters dictionary
        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if min_amount is not None:
            filters["min_amount"] = min_amount
        if max_amount is not None:
            filters["max_amount"] = max_amount
        if status:
            filters["status"] = status
        if currency_type:
            filters["currency_type"] = currency_type
        if transaction_type:
            filters["transaction_type"] = transaction_type
        if direction:
            filters["direction"] = direction
        
        result = await transaction_history_service.export_transactions(
            current_user, db, export_format, filters, search
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export transactions"
        )


@router.get("/export/{export_id}")
async def download_export(
    export_id: str,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=10, window_seconds=60))
):
    """
    Download exported transaction data
    """
    try:
        export_data = transaction_history_service.get_export(export_id)
        
        if not export_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found or expired"
            )
        
        # Set appropriate content type
        if export_data["format"] == "csv":
            content_type = "text/csv"
            filename = f"transactions_{export_id[:8]}.csv"
        else:
            content_type = "application/pdf"
            filename = f"transactions_{export_id[:8]}.pdf"
        
        # Return file response
        return Response(
            content=export_data["data"],
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download export"
        )


@router.get("/export/{export_id}/status", response_model=Dict[str, Any])
async def get_export_status(
    export_id: str,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=20, window_seconds=60))
):
    """
    Get export status and metadata
    """
    try:
        export_data = transaction_history_service.get_export(export_id)
        
        if not export_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found or expired"
            )
        
        return {
            "export_id": export_id,
            "format": export_data["format"],
            "transaction_count": export_data["transaction_count"],
            "created_at": export_data["created_at"].isoformat(),
            "download_url": f"/api/v1/transactions/export/{export_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export status"
        )


@router.post("/cleanup-exports", response_model=ApiResponse)
async def cleanup_expired_exports(
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Clean up expired exports (admin/maintenance endpoint)
    """
    try:
        transaction_history_service.cleanup_expired_exports()
        
        return ApiResponse(
            success=True,
            message="Expired exports cleaned up successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup exports"
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_transaction_summary(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    period: str = Query("30d", description="Summary period (7d, 30d, 90d, 1y)"),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get quick transaction summary
    """
    try:
        if period not in ["7d", "30d", "90d", "1y"]:
            period = "30d"
        
        analytics = await transaction_history_service.get_transaction_analytics(
            current_user, db, period
        )
        
        # Return just the summary part
        return {
            "period": period,
            "summary": analytics.get("summary", {}),
            "status_breakdown": analytics.get("status_breakdown", {}),
            "currency_breakdown": analytics.get("currency_breakdown", {})
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transaction summary"
        )
