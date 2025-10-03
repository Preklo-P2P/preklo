from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from ..database import get_db
from ..models import User, Notification
from ..schemas import Notification as NotificationSchema, ApiResponse
from ..dependencies import require_authentication

router = APIRouter()


@router.get("/user/{user_id}", response_model=List[NotificationSchema])
async def get_user_notifications(
    user_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get notifications for a user"""
    
    # Verify user exists and current user has access
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    notifications = db.query(Notification).filter(
        Notification.user_id == uuid.UUID(user_id)
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    return notifications


@router.put("/{notification_id}/read", response_model=ApiResponse)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    db.commit()
    
    return ApiResponse(
        success=True,
        message="Notification marked as read"
    )


@router.put("/user/{user_id}/read-all", response_model=ApiResponse)
async def mark_all_notifications_as_read(
    user_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for a user"""
    
    # Verify user exists and current user has access
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    db.query(Notification).filter(
        Notification.user_id == uuid.UUID(user_id),
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return ApiResponse(
        success=True,
        message="All notifications marked as read"
    )


# Helper function to create notifications
async def create_notification(
    db: Session,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: dict = None
):
    """Create a new notification"""
    
    notification = Notification(
        user_id=uuid.UUID(user_id),
        type=notification_type,
        title=title,
        message=message,
        data=data
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return notification
