"""
Security Router

API endpoints for advanced security features.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    SecurityEventResponse,
    TrustedDeviceResponse,
    TrustedDeviceCreate,
    BiometricCredentialResponse,
    BiometricCredentialCreate,
    SecurityStatusResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse
)
from app.services.security_service import SecurityService

router = APIRouter()


@router.get("/status", response_model=SecurityStatusResponse)
async def get_security_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive security status for the current user."""
    
    try:
        security_service = SecurityService(db)
        status = security_service.get_security_status(str(current_user.id))
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security status"
        )


@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    event_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get security events for the current user."""
    
    try:
        security_service = SecurityService(db)
        events = security_service.get_security_events(
            user_id=str(current_user.id),
            event_type=event_type,
            limit=limit,
            offset=offset
        )
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events"
        )


@router.post("/events/log")
async def log_security_event(
    event_type: str,
    event_data: Optional[dict] = None,
    risk_score: int = 0,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a security event."""
    
    try:
        security_service = SecurityService(db)
        
        # Extract request information
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        event = security_service.log_security_event(
            user_id=str(current_user.id),
            event_type=event_type,
            event_data=event_data,
            risk_score=risk_score,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {"message": "Security event logged successfully", "event_id": event.id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log security event"
        )


@router.get("/devices", response_model=List[TrustedDeviceResponse])
async def get_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trusted devices for the current user."""
    
    try:
        security_service = SecurityService(db)
        devices = security_service.get_trusted_devices(str(current_user.id))
        return devices
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trusted devices"
        )


@router.post("/devices", response_model=TrustedDeviceResponse)
async def register_trusted_device(
    device_data: TrustedDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new trusted device."""
    
    try:
        security_service = SecurityService(db)
        device = security_service.register_trusted_device(
            user_id=str(current_user.id),
            device_data=device_data
        )
        return device
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register trusted device"
        )


@router.delete("/devices/{device_id}")
async def remove_trusted_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a trusted device."""
    
    try:
        security_service = SecurityService(db)
        success = security_service.remove_trusted_device(
            user_id=str(current_user.id),
            device_id=device_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return {"message": "Device removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove trusted device"
        )


@router.get("/biometric", response_model=List[BiometricCredentialResponse])
async def get_biometric_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get biometric credentials for the current user."""
    
    try:
        security_service = SecurityService(db)
        credentials = security_service.get_biometric_credentials(str(current_user.id))
        return credentials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve biometric credentials"
        )


@router.post("/biometric", response_model=BiometricCredentialResponse)
async def register_biometric_credential(
    credential_data: BiometricCredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new biometric credential."""
    
    try:
        security_service = SecurityService(db)
        credential = security_service.register_biometric_credential(
            user_id=str(current_user.id),
            credential_data=credential_data
        )
        return credential
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register biometric credential"
        )


@router.delete("/biometric/{credential_id}")
async def remove_biometric_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a biometric credential."""
    
    try:
        security_service = SecurityService(db)
        success = security_service.remove_biometric_credential(
            user_id=str(current_user.id),
            credential_id=credential_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        return {"message": "Biometric credential removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove biometric credential"
        )


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_transaction_risk(
    risk_data: RiskAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assess the risk level of a transaction."""
    
    try:
        security_service = SecurityService(db)
        assessment = security_service.assess_transaction_risk(
            user_id=str(current_user.id),
            risk_data=risk_data
        )
        return assessment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assess transaction risk"
        )


@router.post("/device-fingerprint")
async def generate_device_fingerprint(
    user_agent: str,
    screen_resolution: str,
    timezone: str,
    language: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a device fingerprint."""
    
    try:
        security_service = SecurityService(db)
        fingerprint = security_service.generate_device_fingerprint(
            user_agent=user_agent,
            screen_resolution=screen_resolution,
            timezone=timezone,
            language=language
        )
        return {"device_fingerprint": fingerprint}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate device fingerprint"
        )

