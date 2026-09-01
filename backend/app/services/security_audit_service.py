import logging
from typing import Optional, Dict, Any
from app.services.audit_service import AuditService

logger = logging.getLogger("uvicorn.error")


class SecurityAuditService:
    @classmethod
    def log_failed_login(
        cls, email: str, ip_address: Optional[str] = None, reason: str = "Invalid credentials"
    ) -> bool:
        return AuditService.log_event(
            action="AUTH_LOGIN_FAILED",
            event_type="AUTH_LOGIN_FAILED",
            resource_type="AUTH",
            message=f"Failed login attempt for email '{email}'. Reason: {reason}",
            severity="WARNING",
            status="FAILED",
            ip_address=ip_address,
            metadata={"email": email},
        )

    @classmethod
    def log_unauthorized_access(
        cls,
        actor_user_id: Optional[str],
        actor_role: Optional[str],
        resource_type: str,
        resource_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> bool:
        return AuditService.log_event(
            action="UNAUTHORIZED_ACCESS_ATTEMPT",
            event_type="UNAUTHORIZED_ACCESS_ATTEMPT",
            resource_type=resource_type,
            resource_id=resource_id,
            message=f"Unauthorized access attempt by user '{actor_user_id}' ({actor_role}) on endpoint '{endpoint}'",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            severity="ERROR",
            status="FAILED",
            metadata={"endpoint": endpoint},
        )

    @classmethod
    def log_idor_attempt(
        cls,
        actor_user_id: str,
        actor_role: str,
        target_resource_type: str,
        target_resource_id: str,
    ) -> bool:
        return AuditService.log_event(
            action="IDOR_ATTEMPT",
            event_type="IDOR_ATTEMPT",
            resource_type=target_resource_type,
            resource_id=target_resource_id,
            message=f"IDOR attempt detected: User '{actor_user_id}' ({actor_role}) attempted unauthorized access to {target_resource_type} '{target_resource_id}'",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            severity="CRITICAL",
            status="FAILED",
        )
