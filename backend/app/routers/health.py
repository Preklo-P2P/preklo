from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..services.aptos_service import aptos_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint for Railway deployment.
    Returns 200 OK if the API is running.
    This endpoint does not check database connectivity to ensure
    Railway health checks pass even if DB is temporarily unavailable.
    """
    return {
        "status": "healthy",
        "message": "Preklo API is running",
        "version": "1.0.0"
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Preklo API is running"}
