import logging
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import (
    get_current_user,
    require_role,
    require_admin,
    require_teacher,
)
from app.db.mongo import db_manager
from app.schemas.analytics import (
    StudentAnalyticsResponse,
    AttendanceTrendResponse,
    AttendanceTrendPoint,
    StudentRiskResponse,
    ClassAnalyticsResponse,
    SubjectAnalyticsResponse,
    AnalyticsDashboardResponse,
)
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/analytics", tags=["Analytics & Predictive Risk"])


# --- STUDENT ENDPOINTS ---
@router.get(
    "/student/me",
    response_model=StudentAnalyticsResponse,
    summary="Get logged-in student's overall analytics & risk profile",
)
def get_my_analytics(
    current_user: dict = Depends(require_role("STUDENT")),
):
    """Retrieves logged-in student's analytics, status breakdown, and explainable risk factors."""
    db = db_manager.db
    student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
    if not student_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found."
        )

    student_id_str = str(student_doc["_id"])
    from app.services.audit_service import AuditService
    AuditService.log_event(
        action="ANALYTICS_ACCESSED",
        event_type="ANALYTICS_ACCESSED",
        resource_type="ANALYTICS",
        resource_id=student_id_str,
        message="Student accessed personal analytics dashboard",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )
    return AnalyticsService.get_student_analytics(student_id_str)


@router.get(
    "/student/me/trend",
    response_model=AttendanceTrendResponse,
    summary="Get logged-in student's attendance trend",
)
def get_my_trend(
    period_type: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    current_user: dict = Depends(require_role("STUDENT")),
):
    """Retrieves logged-in student's attendance trend (daily/weekly/monthly)."""
    db = db_manager.db
    student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
    if not student_doc:
        return AttendanceTrendResponse(period_type=period_type, points=[])

    student_id_str = str(student_doc["_id"])
    points = AnalyticsService.calculate_student_trend(student_id_str, period_type=period_type)
    return AttendanceTrendResponse(period_type=period_type, points=points)


@router.get(
    "/student/me/subjects",
    response_model=List[dict],
    summary="Get logged-in student's subject-wise analytics",
)
def get_my_subject_analytics(
    current_user: dict = Depends(require_role("STUDENT")),
):
    """Retrieves logged-in student's subject-wise attendance analytics."""
    db = db_manager.db
    student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
    if not student_doc:
        return []

    student_id_str = str(student_doc["_id"])
    st_data = AnalyticsService.get_student_analytics(student_id_str)
    return st_data.get("subject_summaries", [])


# --- ADMIN / TEACHER ENDPOINTS ---
@router.get(
    "/students/{student_id}",
    response_model=StudentAnalyticsResponse,
    summary="Get student analytics (Admin/Teacher)",
)
def get_student_analytics(
    student_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Retrieves analytics and risk profile for a specified student."""
    st_doc = AnalyticsService._get_student_doc(student_id)
    if not st_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found."
        )

    # Teacher authorization check: verify student belongs to teacher's class
    if current_user["role"] == "TEACHER":
        db = db_manager.db
        teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
        assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []

        if not assigned_classes and teacher_doc:
            t_id_str = str(teacher_doc["_id"])
            t_classes = list(db.classes.find({"$or": [{"class_teacher_id": t_id_str}, {"teacher_ids": t_id_str}]}))
            assigned_classes = [str(c["_id"]) for c in t_classes]

        student_class_id = str(st_doc.get("class_id")) if st_doc.get("class_id") else None
        if not student_class_id or student_class_id not in assigned_classes:
            from app.services.security_audit_service import SecurityAuditService
            SecurityAuditService.log_idor_attempt(
                actor_user_id=current_user["id"],
                actor_role=current_user["role"],
                target_resource_type="STUDENT_ANALYTICS",
                target_resource_id=student_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view analytics for this student.",
            )

    return AnalyticsService.get_student_analytics(str(st_doc["_id"]))


@router.get(
    "/classes/{class_id}",
    response_model=ClassAnalyticsResponse,
    summary="Get class-level analytics (Admin/Teacher)",
)
def get_class_analytics(
    class_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Retrieves class-level analytics, average percentage, and risk distribution."""
    # Teacher authorization check
    if current_user["role"] == "TEACHER":
        db = db_manager.db
        teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
        assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []

        if not assigned_classes and teacher_doc:
            t_id_str = str(teacher_doc["_id"])
            t_classes = list(db.classes.find({"$or": [{"class_teacher_id": t_id_str}, {"teacher_ids": t_id_str}]}))
            assigned_classes = [str(c["_id"]) for c in t_classes]

        if str(class_id) not in assigned_classes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned or authorized to view analytics for this class.",
            )

    return AnalyticsService.get_class_analytics(class_id)


@router.get(
    "/classes/{class_id}/subjects/{subject_id}",
    response_model=SubjectAnalyticsResponse,
    summary="Get subject analytics for a class (Admin/Teacher)",
)
def get_class_subject_analytics(
    class_id: str,
    subject_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Retrieves subject-specific analytics for a class."""
    if current_user["role"] == "TEACHER":
        db = db_manager.db
        teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
        assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []
        if str(class_id) not in assigned_classes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized for this class.",
            )

    return AnalyticsService.get_subject_analytics_for_class(class_id, subject_id)


@router.get(
    "/risk-students",
    response_model=List[StudentRiskResponse],
    summary="Get filterable at-risk students list",
)
def get_at_risk_students(
    risk_level: Optional[str] = Query(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    current_user: dict = Depends(require_teacher),
):
    """Retrieves at-risk students list filterable by risk level (LOW/MEDIUM/HIGH/CRITICAL)."""
    allowed_classes = None
    if current_user["role"] == "TEACHER":
        db = db_manager.db
        teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
        allowed_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []

    return AnalyticsService.get_risk_students(risk_level=risk_level, allowed_class_ids=allowed_classes)


@router.get(
    "/dashboard",
    response_model=AnalyticsDashboardResponse,
    summary="Get role-aware dashboard analytics",
)
def get_dashboard_analytics(
    current_user: dict = Depends(get_current_user),
):
    """Retrieves tailored dashboard analytics metrics for Admin, Teacher, or Student."""
    return AnalyticsService.get_dashboard_analytics(current_user)
