from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    ATTENDANCE_LOW = "ATTENDANCE_LOW"
    RISK_HIGH = "RISK_HIGH"
    RISK_CRITICAL = "RISK_CRITICAL"
    ATTENDANCE_SESSION = "ATTENDANCE_SESSION"
    REPORT_READY = "REPORT_READY"
    SYSTEM = "SYSTEM"


class NotificationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationResponse(BaseModel):
    id: str
    recipient_user_id: str
    notification_type: NotificationType
    title: str
    message: str
    severity: NotificationSeverity
    is_read: bool = False
    context_key: Optional[str] = None
    created_at: datetime
    related_student_id: Optional[str] = None
    related_class_id: Optional[str] = None
    related_subject_id: Optional[str] = None
    related_session_id: Optional[str] = None


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int


class NotificationPreferenceResponse(BaseModel):
    user_id: str
    in_app_enabled: bool = True
    email_enabled: bool = True
    low_attendance_enabled: bool = True
    risk_alert_enabled: bool = True
    report_notifications_enabled: bool = True
    updated_at: datetime


class NotificationPreferenceUpdateRequest(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    low_attendance_enabled: Optional[bool] = None
    risk_alert_enabled: Optional[bool] = None
    report_notifications_enabled: Optional[bool] = None
