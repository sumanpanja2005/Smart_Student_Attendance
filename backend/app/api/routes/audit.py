import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import require_admin
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditSummaryResponse,
    SecurityEventResponse,
    AuditSeverity,
    AuditStatus,
)
from app.services.audit_repository import AuditRepository

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/admin", tags=["Audit Trail & Observability"])


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="List filterable audit logs (Admin-Only)",
)
def list_audit_logs(
    actor_user_id: Optional[str] = Query(None),
    actor_role: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    severity: Optional[AuditSeverity] = Query(None),
    status_val: Optional[AuditStatus] = Query(None, alias="status"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_admin),
):
    """Retrieves paginated, filterable audit logs. Guarded with Admin authorization."""
    filters = {
        "actor_user_id": actor_user_id,
        "actor_role": actor_role,
        "event_type": event_type,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "severity": severity,
        "status": status_val,
        "start_date": start_date,
        "end_date": end_date,
    }

    logs, total_count = AuditRepository.list_audit_logs(filters, page=page, limit=limit)
    return AuditLogListResponse(
        audit_logs=logs,
        total_count=total_count,
        page=page,
        limit=min(100, max(1, limit)),
    )


@router.get(
    "/audit-logs/{audit_id}",
    response_model=AuditLogResponse,
    summary="Get single audit log entry (Admin-Only)",
)
def get_audit_log(
    audit_id: str,
    current_user: dict = Depends(require_admin),
):
    """Retrieves single audit log entry by ID."""
    doc = AuditRepository.get_audit_log(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audit log entry not found."
        )
    return doc


@router.get(
    "/audit-summary",
    response_model=AuditSummaryResponse,
    summary="Get audit event summary statistics (Admin-Only)",
)
def get_audit_summary(
    current_user: dict = Depends(require_admin),
):
    """Retrieves aggregate summary of audit event counts and distributions."""
    return AuditRepository.get_audit_summary()


@router.get(
    "/security-events",
    response_model=List[SecurityEventResponse],
    summary="Get security events log (Admin-Only)",
)
def get_security_events(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_admin),
):
    """Retrieves high-severity security events log."""
    return AuditRepository.get_security_events(limit=limit)


@router.delete(
    "/audit-logs/retention",
    summary="Delete old audit logs based on retention policy (Admin-Only)",
)
def clean_audit_log_retention(
    retention_days: int = Query(365, ge=7, le=3650),
    current_user: dict = Depends(require_admin),
):
    """Deletes audit records older than specified retention days. Requires Admin authorization."""
    deleted_count = AuditRepository.delete_old_audit_logs(retention_days=retention_days)
    return {
        "success": True,
        "message": f"Successfully deleted {deleted_count} audit log entries older than {retention_days} days.",
        "deleted_count": deleted_count,
        "retention_days": retention_days,
    }
