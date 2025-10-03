"""
Security Service

Handles advanced security features including biometric authentication,
device management, fraud detection, and security monitoring.
"""

import uuid
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models import SecurityEvent, TrustedDevice, BiometricCredential, User
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
from app.config import settings
from app.services.notification_service import NotificationService


class SecurityService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def log_security_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        risk_score: int = 0,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None,
        location_data: Optional[Dict[str, Any]] = None
    ) -> SecurityEventResponse:
        """Log a security event."""
        
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            risk_score=risk_score,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            location_data=location_data,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Send notification for high-risk events
        if risk_score >= 70:
            self._send_security_alert(user_id, event)
        
        return self._format_security_event_response(event)
    
    def get_security_events(
        self,
        user_id: str,
        event_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SecurityEventResponse]:
        """Get security events for a user."""
        
        query = self.db.query(SecurityEvent).filter(SecurityEvent.user_id == user_id)
        
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        
        events = query.order_by(desc(SecurityEvent.created_at)).offset(offset).limit(limit).all()
        
        return [self._format_security_event_response(event) for event in events]
    
    def register_trusted_device(
        self,
        user_id: str,
        device_data: TrustedDeviceCreate
    ) -> TrustedDeviceResponse:
        """Register a new trusted device."""
        
        # Check if device already exists
        existing_device = self.db.query(TrustedDevice).filter(
            and_(
                TrustedDevice.user_id == user_id,
                TrustedDevice.device_fingerprint == device_data.device_fingerprint
            )
        ).first()
        
        if existing_device:
            # Update existing device
            existing_device.device_name = device_data.device_name
            existing_device.device_type = device_data.device_type
            existing_device.is_trusted = True
            existing_device.last_used_at = datetime.now(timezone.utc)
            existing_device.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(existing_device)
            
            return self._format_trusted_device_response(existing_device)
        
        # Create new device
        device = TrustedDevice(
            id=str(uuid.uuid4()),
            user_id=user_id,
            device_name=device_data.device_name,
            device_fingerprint=device_data.device_fingerprint,
            device_type=device_data.device_type,
            is_trusted=True,
            last_used_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        
        # Log security event
        self.log_security_event(
            user_id=user_id,
            event_type="device_trusted",
            event_data={
                "device_name": device_data.device_name,
                "device_type": device_data.device_type
            },
            risk_score=10,
            device_id=device_data.device_fingerprint
        )
        
        return self._format_trusted_device_response(device)
    
    def get_trusted_devices(self, user_id: str) -> List[TrustedDeviceResponse]:
        """Get trusted devices for a user."""
        
        devices = self.db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id
        ).order_by(desc(TrustedDevice.last_used_at)).all()
        
        return [self._format_trusted_device_response(device) for device in devices]
    
    def remove_trusted_device(self, user_id: str, device_id: str) -> bool:
        """Remove a trusted device."""
        
        device = self.db.query(TrustedDevice).filter(
            and_(
                TrustedDevice.id == device_id,
                TrustedDevice.user_id == user_id
            )
        ).first()
        
        if not device:
            return False
        
        # Log security event
        self.log_security_event(
            user_id=user_id,
            event_type="device_removed",
            event_data={
                "device_name": device.device_name,
                "device_type": device.device_type
            },
            risk_score=20,
            device_id=device.device_fingerprint
        )
        
        self.db.delete(device)
        self.db.commit()
        
        return True
    
    def register_biometric_credential(
        self,
        user_id: str,
        credential_data: BiometricCredentialCreate
    ) -> BiometricCredentialResponse:
        """Register a new biometric credential."""
        
        # Check if credential already exists
        existing_credential = self.db.query(BiometricCredential).filter(
            and_(
                BiometricCredential.user_id == user_id,
                BiometricCredential.credential_id == credential_data.credential_id
            )
        ).first()
        
        if existing_credential:
            # Update existing credential
            existing_credential.credential_type = credential_data.credential_type
            existing_credential.public_key = credential_data.public_key
            existing_credential.is_active = True
            existing_credential.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(existing_credential)
            
            return self._format_biometric_credential_response(existing_credential)
        
        # Create new credential
        credential = BiometricCredential(
            id=str(uuid.uuid4()),
            user_id=user_id,
            credential_type=credential_data.credential_type,
            credential_id=credential_data.credential_id,
            public_key=credential_data.public_key,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(credential)
        self.db.commit()
        self.db.refresh(credential)
        
        # Log security event
        self.log_security_event(
            user_id=user_id,
            event_type="biometric_registered",
            event_data={
                "credential_type": credential_data.credential_type
            },
            risk_score=5
        )
        
        return self._format_biometric_credential_response(credential)
    
    def get_biometric_credentials(self, user_id: str) -> List[BiometricCredentialResponse]:
        """Get biometric credentials for a user."""
        
        credentials = self.db.query(BiometricCredential).filter(
            and_(
                BiometricCredential.user_id == user_id,
                BiometricCredential.is_active == True
            )
        ).order_by(desc(BiometricCredential.created_at)).all()
        
        return [self._format_biometric_credential_response(credential) for credential in credentials]
    
    def remove_biometric_credential(self, user_id: str, credential_id: str) -> bool:
        """Remove a biometric credential."""
        
        credential = self.db.query(BiometricCredential).filter(
            and_(
                BiometricCredential.id == credential_id,
                BiometricCredential.user_id == user_id
            )
        ).first()
        
        if not credential:
            return False
        
        # Log security event
        self.log_security_event(
            user_id=user_id,
            event_type="biometric_removed",
            event_data={
                "credential_type": credential.credential_type
            },
            risk_score=15
        )
        
        credential.is_active = False
        credential.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return True
    
    def get_security_status(self, user_id: str) -> SecurityStatusResponse:
        """Get comprehensive security status for a user."""
        
        # Get biometric credentials
        biometric_credentials = self.get_biometric_credentials(user_id)
        has_biometric_auth = len(biometric_credentials) > 0
        
        # Get trusted devices
        trusted_devices = self.get_trusted_devices(user_id)
        trusted_devices_count = len([d for d in trusted_devices if d.is_trusted])
        
        # Get last security event
        last_event = self.db.query(SecurityEvent).filter(
            SecurityEvent.user_id == user_id
        ).order_by(desc(SecurityEvent.created_at)).first()
        
        last_security_event = None
        if last_event:
            last_security_event = self._format_security_event_response(last_event)
        
        # Calculate overall risk score
        risk_score = self._calculate_user_risk_score(user_id)
        
        # Generate security recommendations
        recommendations = self._generate_security_recommendations(
            user_id, has_biometric_auth, trusted_devices_count, risk_score
        )
        
        return SecurityStatusResponse(
            user_id=user_id,
            has_biometric_auth=has_biometric_auth,
            trusted_devices_count=trusted_devices_count,
            last_security_event=last_security_event,
            risk_score=risk_score,
            security_recommendations=recommendations,
            mfa_enabled=has_biometric_auth,  # Simplified for now
            session_timeout_minutes=30
        )
    
    def assess_transaction_risk(
        self,
        user_id: str,
        risk_data: RiskAssessmentRequest
    ) -> RiskAssessmentResponse:
        """Assess the risk level of a transaction."""
        
        risk_factors = []
        risk_score = 0
        
        # Amount-based risk
        if risk_data.transaction_amount:
            if risk_data.transaction_amount > 1000:
                risk_score += 20
                risk_factors.append("High transaction amount")
            elif risk_data.transaction_amount > 500:
                risk_score += 10
                risk_factors.append("Medium transaction amount")
        
        # Device-based risk
        if risk_data.device_fingerprint:
            device = self.db.query(TrustedDevice).filter(
                and_(
                    TrustedDevice.user_id == user_id,
                    TrustedDevice.device_fingerprint == risk_data.device_fingerprint,
                    TrustedDevice.is_trusted == True
                )
            ).first()
            
            if not device:
                risk_score += 30
                risk_factors.append("Untrusted device")
            else:
                # Check if device was used recently
                if device.last_used_at and (datetime.now(timezone.utc) - device.last_used_at).days > 30:
                    risk_score += 15
                    risk_factors.append("Device not used recently")
        
        # Location-based risk (if available)
        if risk_data.location_data:
            # Check for unusual location patterns
            recent_events = self.db.query(SecurityEvent).filter(
                and_(
                    SecurityEvent.user_id == user_id,
                    SecurityEvent.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
                )
            ).all()
            
            # Simple location risk assessment
            if len(recent_events) > 10:  # High activity
                risk_score += 10
                risk_factors.append("High account activity")
        
        # Transaction type risk
        if risk_data.transaction_type:
            if risk_data.transaction_type in ["withdrawal", "transfer"]:
                risk_score += 15
                risk_factors.append("High-risk transaction type")
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate recommendations
        recommendations = []
        if risk_score >= 50:
            recommendations.append("Consider using biometric authentication")
        if risk_score >= 30:
            recommendations.append("Verify transaction details carefully")
        if not risk_data.device_fingerprint or risk_score >= 40:
            recommendations.append("Use a trusted device for this transaction")
        
        return RiskAssessmentResponse(
            risk_score=min(risk_score, 100),
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendations=recommendations,
            requires_additional_auth=risk_score >= 50,
            estimated_processing_time=5 if risk_score < 30 else 15
        )
    
    def generate_device_fingerprint(
        self,
        user_agent: str,
        screen_resolution: str,
        timezone: str,
        language: str
    ) -> str:
        """Generate a unique device fingerprint."""
        
        fingerprint_data = f"{user_agent}|{screen_resolution}|{timezone}|{language}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    def _calculate_user_risk_score(self, user_id: str) -> int:
        """Calculate overall user risk score."""
        
        # Get recent security events
        recent_events = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.user_id == user_id,
                SecurityEvent.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
            )
        ).all()
        
        if not recent_events:
            return 10  # Low risk for new users
        
        # Calculate average risk score
        total_risk = sum(event.risk_score for event in recent_events)
        avg_risk = total_risk / len(recent_events)
        
        # Adjust based on event frequency
        if len(recent_events) > 20:
            avg_risk += 10  # High activity increases risk
        
        return min(int(avg_risk), 100)
    
    def _generate_security_recommendations(
        self,
        user_id: str,
        has_biometric_auth: bool,
        trusted_devices_count: int,
        risk_score: int
    ) -> List[str]:
        """Generate security recommendations for a user."""
        
        recommendations = []
        
        if not has_biometric_auth:
            recommendations.append("Enable biometric authentication for enhanced security")
        
        if trusted_devices_count == 0:
            recommendations.append("Add trusted devices to your account")
        elif trusted_devices_count > 5:
            recommendations.append("Consider removing unused trusted devices")
        
        if risk_score > 50:
            recommendations.append("Review recent account activity")
        
        if risk_score > 70:
            recommendations.append("Enable additional security measures")
        
        return recommendations
    
    def _send_security_alert(self, user_id: str, event: SecurityEvent):
        """Send security alert notification."""
        
        self.notification_service.create_notification(
            user_id=user_id,
            title="Security Alert",
            message=f"High-risk security event detected: {event.event_type}",
            type="security_alert",
            data={
                "event_type": event.event_type,
                "risk_score": event.risk_score,
                "timestamp": event.created_at.isoformat()
            }
        )
    
    def _format_security_event_response(self, event: SecurityEvent) -> SecurityEventResponse:
        """Format security event for response."""
        
        return SecurityEventResponse(
            id=event.id,
            user_id=event.user_id,
            event_type=event.event_type,
            event_data=event.event_data,
            risk_score=event.risk_score,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            device_id=event.device_id,
            location_data=event.location_data,
            created_at=event.created_at
        )
    
    def _format_trusted_device_response(self, device: TrustedDevice) -> TrustedDeviceResponse:
        """Format trusted device for response."""
        
        return TrustedDeviceResponse(
            id=device.id,
            user_id=device.user_id,
            device_name=device.device_name,
            device_fingerprint=device.device_fingerprint,
            device_type=device.device_type,
            is_trusted=device.is_trusted,
            last_used_at=device.last_used_at,
            created_at=device.created_at,
            updated_at=device.updated_at
        )
    
    def _format_biometric_credential_response(self, credential: BiometricCredential) -> BiometricCredentialResponse:
        """Format biometric credential for response."""
        
        return BiometricCredentialResponse(
            id=credential.id,
            user_id=credential.user_id,
            credential_type=credential.credential_type,
            credential_id=credential.credential_id,
            is_active=credential.is_active,
            created_at=credential.created_at,
            updated_at=credential.updated_at
        )

