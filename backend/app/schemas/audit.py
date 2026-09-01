from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class AuditSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    WARNING = "WARNING"


class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    actor_user_id: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    event_type: str
    resource_type: str
    resource_id: Optional[str] = None
    severity: AuditSeverity = AuditSeverity.INFO
    status: AuditStatus = AuditStatus.SUCCESS
    message: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditLogListResponse(BaseModel):
    audit_logs: List[AuditLogResponse]
    total_count: int
    page: int
    limit: int


class AuditLogFilterRequest(BaseModel):
    actor_user_id: Optional[str] = None
    actor_role: Optional[str] = None
    event_type: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    severity: Optional[AuditSeverity] = None
    status: Optional[AuditStatus] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    limit: int = 50


class AuditSummaryResponse(BaseModel):
    total_audit_events: int
    auth_events_count: int
    attendance_events_count: int
    security_events_count: int
    system_events_count: int
    event_type_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]


class SecurityEventResponse(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    actor_user_id: Optional[str] = None
    actor_role: Optional[str] = None
    severity: AuditSeverity
    message: str
    ip_address: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None


class SystemHealthResponse(BaseModel):
    status: str
    database: str
    database_latency_ms: float
    uptime_seconds: float
    timestamp: datetime
    face_model: str


class SystemMetricsResponse(BaseModel):
    total_users: int
    active_users: int
    total_students: int
    total_teachers: int
    total_classes: int
    total_subjects: int
    open_attendance_sessions: int
    total_attendance_records: int
    notification_count: int
    generated_report_count: int
    audit_event_count: int
