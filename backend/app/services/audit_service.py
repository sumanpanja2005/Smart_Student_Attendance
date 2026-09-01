import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.services.audit_repository import AuditRepository

logger = logging.getLogger("uvicorn.error")


class AuditService:
    @classmethod
    def log_event(
        cls,
        action: str,
        event_type: str,
        resource_type: str,
        message: str,
        actor_user_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: str = "INFO",
        status: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Failure-safe audit logger method.
        NEVER raises exceptions or interrupts caller execution.
        """
        try:
            doc = {
                "timestamp": datetime.now(timezone.utc),
                "actor_user_id": str(actor_user_id) if actor_user_id else None,
                "actor_role": actor_role,
                "action": action,
                "event_type": event_type,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "severity": severity,
                "status": status,
                "message": message,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "metadata": metadata or {},
            }
            succ, _ = AuditRepository.create_audit_log(doc)
            return succ
        except Exception as exc:
            logger.error(f"AuditService.log_event failed gracefully: {exc}")
            return False

    # --- SPECIFIC EVENT LOGGING HELPERS ---
    @classmethod
    def log_auth_event(
        cls,
        event_type: str,
        message: str,
        actor_user_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        status: str = "SUCCESS",
        severity: str = "INFO",
        ip_address: Optional[str] = None,
    ) -> bool:
        return cls.log_event(
            action=event_type,
            event_type=event_type,
            resource_type="AUTH",
            message=message,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            status=status,
            severity=severity,
            ip_address=ip_address,
        )

    @classmethod
    def log_face_event(
        cls,
        event_type: str,
        message: str,
        actor_user_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        student_id: Optional[str] = None,
        status: str = "SUCCESS",
        severity: str = "INFO",
    ) -> bool:
        """Logs safe face registration/recognition events (NEVER stores biometric vectors)."""
        return cls.log_event(
            action=event_type,
            event_type=event_type,
            resource_type="FACE_PROFILE",
            resource_id=student_id,
            message=message,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            status=status,
            severity=severity,
        )

    @classmethod
    def log_attendance_event(
        cls,
        event_type: str,
        message: str,
        actor_user_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        session_id: Optional[str] = None,
        status: str = "SUCCESS",
        severity: str = "INFO",
    ) -> bool:
        return cls.log_event(
            action=event_type,
            event_type=event_type,
            resource_type="ATTENDANCE_SESSION",
            resource_id=session_id,
            message=message,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            status=status,
            severity=severity,
        )
