"""
Notification Service
Handles user notifications and alerts
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.models import User, Notification
from app.schemas import NotificationCreate, NotificationResponse


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self, 
        user_id: str, 
        title: str, 
        message: str, 
        notification_type: str = "info"
    ) -> Notification:
        """Create a new notification for a user"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return notification

    def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a user"""
        return self.db.query(Notification)\
            .filter(Notification.user_id == user_id)\
            .order_by(Notification.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()

    def mark_notification_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        notification = self.db.query(Notification)\
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )\
            .first()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        
        return False

    def mark_all_notifications_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        updated_count = self.db.query(Notification)\
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )\
            .update({
                "is_read": True,
                "read_at": datetime.now(timezone.utc)
            })
        
        self.db.commit()
        return updated_count

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        return self.db.query(Notification)\
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )\
            .count()

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        notification = self.db.query(Notification)\
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )\
            .first()
        
        if notification:
            self.db.delete(notification)
            self.db.commit()
            return True
        
        return False
