import time
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import require_admin
from app.db.mongo import db_manager
from app.schemas.audit import SystemHealthResponse, SystemMetricsResponse
from app.services.face_service import get_model_status

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/admin/system", tags=["System Operational Monitoring"])

START_TIME = time.time()


@router.get(
    "/health",
    response_model=SystemHealthResponse,
    summary="Get extended operational system health (Admin-Only)",
)
def get_system_health(
    current_user: dict = Depends(require_admin),
):
    """
    Returns extended operational system health, database latency (in ms), and application uptime.
    Guarded with Admin authorization.
    """
    db_status = db_manager.get_status()

    # Measure DB latency
    latency_ms = 0.0
    if db_status == "connected" and db_manager.db is not None:
        t0 = time.time()
        try:
            db_manager.db.command("ping")
            latency_ms = round((time.time() - t0) * 1000.0, 2)
        except Exception:
            latency_ms = 0.0

    uptime_sec = round(time.time() - START_TIME, 1)
    face_status = get_model_status()

    return SystemHealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        database_latency_ms=latency_ms,
        uptime_seconds=uptime_sec,
        timestamp=datetime.now(timezone.utc),
        face_model=face_status,
    )


@router.get(
    "/metrics",
    response_model=SystemMetricsResponse,
    summary="Get system operational metrics (Admin-Only)",
)
def get_system_metrics(
    current_user: dict = Depends(require_admin),
):
    """Returns system entity counters and operational metrics. Guarded with Admin authorization."""
    db = db_manager.db
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database connection unavailable."
        )

    total_users = db.users.count_documents({})
    active_users = db.users.count_documents({"is_active": True})
    total_students = db.students.count_documents({})
    total_teachers = db.teachers.count_documents({})
    total_classes = db.classes.count_documents({})
    total_subjects = db.subjects.count_documents({})
    open_sessions = db.attendance_sessions.count_documents({"status": "OPEN"})
    total_records = db.attendance_records.count_documents({})
    notif_count = db.notifications.count_documents({})
    report_count = db.generated_reports.count_documents({})
    audit_count = db.audit_logs.count_documents({})

    return SystemMetricsResponse(
        total_users=total_users,
        active_users=active_users,
        total_students=total_students,
        total_teachers=total_teachers,
        total_classes=total_classes,
        total_subjects=total_subjects,
        open_attendance_sessions=open_sessions,
        total_attendance_records=total_records,
        notification_count=notif_count,
        generated_report_count=report_count,
        audit_event_count=audit_count,
    )
