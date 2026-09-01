import os
import logging
from typing import Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from app.api.deps import (
    get_current_user,
    require_role,
    require_admin,
    require_teacher,
)
from app.db.mongo import db_manager
from app.schemas.report import (
    StudentReportRequest,
    ClassReportRequest,
    SubjectReportRequest,
    ReportMetadataResponse,
)
from app.services.report_service import ReportService

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/reports", tags=["Reporting & PDF Downloads"])


@router.post(
    "/student",
    response_model=ReportMetadataResponse,
    summary="Generate student attendance PDF report",
)
def generate_student_report(
    payload: StudentReportRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generates a student attendance PDF report.
    Students can generate ONLY their own report. Teachers can generate for assigned students.
    """
    db = db_manager.db
    target_student_id = payload.student_id

    if current_user["role"] == "STUDENT":
        st_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
        if not st_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found."
            )
        target_student_id = str(st_doc["_id"])
    elif not target_student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="student_id parameter is required."
        )

    # Teacher authorization check
    if current_user["role"] == "TEACHER":
        st_doc = db.students.find_one({"_id": ObjectId(target_student_id)})
        if not st_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")
        teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
        assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []
        if str(st_doc.get("class_id")) not in assigned_classes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to generate a report for this student.",
            )

    return ReportService.generate_student_report(
        current_user=current_user,
        student_id=target_student_id,
        date_from=payload.date_from,
        date_to=payload.date_to,
        subject_id=payload.subject_id,
    )


@router.post(
    "/class",
    response_model=ReportMetadataResponse,
    summary="Generate class attendance PDF report (Admin/Teacher)",
)
def generate_class_report(
    payload: ClassReportRequest,
    current_user: dict = Depends(require_teacher),
):
    """Generates a class attendance roster PDF report."""
    if current_user["role"] == "TEACHER":
        db = db_manager.db
        teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
        assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []
        if str(payload.class_id) not in assigned_classes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to generate reports for this class.",
            )

    return ReportService.generate_class_report(
        current_user=current_user,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )


@router.post(
    "/subject",
    response_model=ReportMetadataResponse,
    summary="Generate subject attendance PDF report (Admin/Teacher)",
)
def generate_subject_report(
    payload: SubjectReportRequest,
    current_user: dict = Depends(require_teacher),
):
    """Generates a subject attendance statistics PDF report."""
    if current_user["role"] == "TEACHER":
        db = db_manager.db
        teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
        assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []
        if str(payload.class_id) not in assigned_classes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized for this class.",
            )

    return ReportService.generate_subject_report(
        current_user=current_user,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )


@router.post(
    "/analytics",
    response_model=ReportMetadataResponse,
    summary="Generate analytics/risk PDF report",
)
def generate_analytics_report(
    student_id: Optional[str] = None,
    class_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Generates a predictive risk & analytics PDF report."""
    db = db_manager.db
    target_student_id = student_id

    if current_user["role"] == "STUDENT":
        st_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
        if not st_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found."
            )
        target_student_id = str(st_doc["_id"])
        class_id = None
    elif current_user["role"] == "TEACHER":
        if class_id:
            teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
            assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []
            if str(class_id) not in assigned_classes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized for this class.",
                )

    return ReportService.generate_analytics_report(
        current_user=current_user,
        student_id=target_student_id,
        class_id=class_id,
    )


@router.get(
    "/{report_id}",
    summary="Download generated PDF report (Secure Endpoint)",
)
def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Secure PDF download endpoint.
    Retrieves report document from MongoDB and independently verifies authorization (prevents IDOR).
    """
    db = db_manager.db
    try:
        report_doc = db.generated_reports.find_one({"_id": ObjectId(report_id)})
    except Exception:
        report_doc = None

    if not report_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report document not found."
        )

    # Secure Authorization Checks (Prevents IDOR)
    user_id = current_user["id"]
    role = current_user["role"]

    if role == "STUDENT":
        st_doc = db.students.find_one({"user_id": ObjectId(user_id)})
        st_id_str = str(st_doc["_id"]) if st_doc else None
        if report_doc.get("generated_by") != user_id and report_doc.get("student_id") != st_id_str:
            from app.services.security_audit_service import SecurityAuditService
            SecurityAuditService.log_idor_attempt(
                actor_user_id=user_id,
                actor_role=role,
                target_resource_type="REPORT",
                target_resource_id=report_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to download this report.",
            )
    elif role == "TEACHER":
        teacher_doc = db.teachers.find_one({"user_id": ObjectId(user_id)})
        assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []

        is_owner = report_doc.get("generated_by") == user_id
        is_class_auth = report_doc.get("class_id") in assigned_classes

        # Student check
        is_st_auth = False
        if report_doc.get("student_id"):
            st_doc = db.students.find_one({"_id": ObjectId(report_doc["student_id"])})
            if st_doc and str(st_doc.get("class_id")) in assigned_classes:
                is_st_auth = True

        if not (is_owner or is_class_auth or is_st_auth):
            from app.services.security_audit_service import SecurityAuditService
            SecurityAuditService.log_idor_attempt(
                actor_user_id=user_id,
                actor_role=role,
                target_resource_type="REPORT",
                target_resource_id=report_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to download this report.",
            )

    file_path = report_doc.get("file_path")
    file_name = report_doc.get("file_name", "report.pdf")

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated PDF file does not exist on server storage.",
        )

    # Path Traversal Prevention Check (Runs before file existence check for security)
    from app.core.config import settings
    base_reports_dir = os.path.normcase(os.path.abspath(settings.REPORTS_DIR))
    target_abs_path = os.path.normcase(os.path.abspath(file_path))

    if not target_abs_path.startswith(base_reports_dir):
        logger.error(f"Path traversal check failed. target={target_abs_path}, base={base_reports_dir}")
        from app.services.security_audit_service import SecurityAuditService
        SecurityAuditService.log_idor_attempt(
            actor_user_id=user_id,
            actor_role=role,
            target_resource_type="REPORT",
            target_resource_id=report_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Invalid file path target.",
        )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated PDF file does not exist on server storage.",
        )

    from app.services.audit_service import AuditService
    AuditService.log_event(
        action="REPORT_DOWNLOADED",
        event_type="REPORT_DOWNLOADED",
        resource_type="REPORT",
        resource_id=report_id,
        message=f"User downloaded report {file_name}",
        actor_user_id=user_id,
        actor_role=role,
    )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_name,
    )
